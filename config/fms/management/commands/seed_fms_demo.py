"""Create a deterministic, local-only FMS dataset through real accounting flows."""
from datetime import date, datetime, time, timedelta
from decimal import Decimal

from django.apps import apps
from django.conf import settings
from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models import Q
from django.test.utils import override_settings
from django.utils import timezone

from academic.models import CourseType
from accounts.models import User, StudentProfile, InstructorProfile, StaffProfile
from fleet.models import Aircraft
from fms.forms import FlightEvaluation0_100Form, FlightEvaluation100_120Form, FlightEvaluation120_170Form
from transactions.models import StudentTransaction
from transactions.services import record_late_fuel
from transactions.student_activity import FLIGHT_MODELS, student_activity


MARKER = '[seed_fms_demo:v1]'
GROUP = 'FMS demo dataset v1'
PASSWORD = 'navdemo26%'
ACCOUNTS = (
    ('demo_fms_student', 99001001, 'STUDENT', 'Ana', 'Actividad'),
    ('demo_fms_advanced', 99001002, 'STUDENT', 'Luis', 'Avanzado'),
    ('demo_fms_debt', 99001003, 'STUDENT', 'Eva', 'Saldo negativo'),
    ('demo_fms_empty', 99001004, 'STUDENT', 'Leo', 'Sin actividad'),
    ('demo_fms_instructor', 99001005, 'INSTRUCTOR', 'Carlos', 'Instructor'),
    ('demo_fms_staff', 99001006, 'STAFF', 'Sofia', 'Administración'),
)
AIRCRAFT = ('DEMO-FMS-01', 'DEMO-FMS-02')
COURSES = ('PPA-P', 'HVI-P', 'PCA-P')


class Command(BaseCommand):
    help = 'Seed local FMS demo accounts, flights and transactions; never runs in production.'

    def add_arguments(self, parser):
        """Expose a reproducible scenario date and an explicitly scoped reset."""
        parser.add_argument('--reset', action='store_true', help='Replace seed-owned activity; refuse to erase manual test activity.')
        parser.add_argument('--as-of', type=date.fromisoformat, default=None, help='Scenario end date (YYYY-MM-DD); defaults to today.')

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.dummy.EmailBackend')
    def handle(self, *args, **options):
        """Seed atomically with all signal-generated emails discarded locally.

        The temporary email backend covers writes and commit callbacks, and is
        restored even if validation fails. Normal application mail settings are
        not changed by running this command.
        """
        if not settings.DEBUG or getattr(settings, 'ON_PYTHONANYWHERE', False):
            raise CommandError('Demo seeding is disabled in production (requires DEBUG=True and IS_PRODUCTION=false).')
        self.as_of = options['as_of'] or timezone.localdate()
        if isinstance(self.as_of, str):
            try:
                self.as_of = date.fromisoformat(self.as_of)
            except ValueError as exc:
                raise CommandError('Use --as-of YYYY-MM-DD.') from exc
        with transaction.atomic():
            exists = self.check_ownership()
            if exists and not options['reset']:
                self.stdout.write('Demo dataset already exists. No records or passwords changed. Use --reset to rebuild.')
            else:
                if exists:
                    self.reset_activity()
                self.create_accounts()
                self.create_aircraft()
                self.seed_scenarios()
                self.stdout.write(self.style.SUCCESS('FMS demo dataset ready.'))
        self.print_summary()

    def check_ownership(self):
        """Reject reserved identities that are not the complete, marked dataset.

        The dedicated group marks account ownership; aircraft carry the same
        dataset marker in notes and their reserved serial numbers. Never adopt
        an existing account or aircraft merely because its name matches.
        """
        group = Group.objects.filter(name=GROUP).first()
        found = []
        for username, national_id, role, _, _ in ACCOUNTS:
            matches = User.objects.filter(Q(username=username) | Q(national_id=national_id) | Q(email=f'{username}@example.invalid'))
            for user in matches:
                if (not group or user.username != username or user.national_id != national_id
                        or user.email != f'{username}@example.invalid' or user.role != role
                        or not user.groups.filter(pk=group.pk).exists()):
                    raise CommandError(f'Reserved demo identity conflicts with an existing account: {username}. Nothing changed.')
                found.append(user.pk)
        planes = Aircraft.objects.filter(Q(registration__in=AIRCRAFT) | Q(serial_number__in=AIRCRAFT))
        for plane in planes:
            if not group or plane.registration not in AIRCRAFT or plane.serial_number != plane.registration or plane.notes != MARKER:
                raise CommandError('Reserved demo aircraft conflicts with existing data. Nothing changed.')
        if group and (len(found) != len(ACCOUNTS) or group.user_set.count() != len(ACCOUNTS) or planes.count() != 2):
            raise CommandError('Demo dataset is incomplete or its ownership markers changed. Review it before seeding.')
        return bool(group)

    def reset_activity(self):
        """Remove only marked demo activity, keeping account and aircraft identities.

        Refuse reset if manual FMS activity uses a demo student, instructor or
        aircraft, or if a transaction lacks the seed marker. Queryset deletion
        intentionally skips per-flight refunds: demo balances and totals are
        rebuilt from zero in the same transaction, rather than refunded twice.
        """
        user_ids = [account[1] for account in ACCOUNTS]
        seed_models = {model for _, model in FLIGHT_MODELS}
        for model in apps.get_app_config('fms').get_models():
            fields = {field.name for field in model._meta.fields}
            scope = Q()
            if 'student_id' in fields:
                scope |= Q(student_id__in=user_ids)
            if 'instructor_id' in fields:
                scope |= Q(instructor_id__in=user_ids)
            if 'aircraft' in fields:
                scope |= Q(aircraft__registration__in=AIRCRAFT)
            if not scope:
                continue
            records = model.objects.filter(scope)
            if model not in seed_models:
                unsafe = records.exists()
            else:
                unsafe = records.exclude(
                    comments__startswith=MARKER, student_id__in=user_ids[:4],
                    instructor_id=user_ids[4], aircraft__registration__in=AIRCRAFT,
                ).exists()
            if unsafe:
                raise CommandError('Reset refused: manual or non-demo flight activity references demo records. Nothing changed.')
        movements = StudentTransaction.objects.filter(
            Q(student_profile__user__national_id__in=user_ids) |
            Q(added_by__national_id__in=user_ids) | Q(confirmed_by__national_id__in=user_ids)
        )
        if movements.exclude(notes__contains=MARKER, student_profile__user__national_id__in=user_ids[:4]).exists():
            raise CommandError('Reset refused: manual or non-demo transactions reference demo accounts. Nothing changed.')
        movements.delete()
        for _, model in FLIGHT_MODELS:
            records = model.objects.filter(student_id__in=user_ids[:4], comments__startswith=MARKER)
            if records.filter(aura_review__isnull=False).exists():
                raise CommandError('Reset refused: demo flights have AURA reviews. Nothing changed.')
            records.delete()

    def create_accounts(self):
        """Create marked demo logins and reset their starting profile values."""
        group, _ = Group.objects.get_or_create(name=GROUP)
        self.users = {}
        for username, national_id, role, first, last in ACCOUNTS:
            user, _ = User.objects.get_or_create(username=username, defaults={
                'email': f'{username}@example.invalid', 'national_id': national_id,
                'role': role, 'first_name': first, 'last_name': f'DEMO {last}',
            })
            user.set_password(PASSWORD)
            user.is_active = True
            user.is_staff = role == 'STAFF'
            user.save()
            user.groups.add(group)
            self.users[username] = user
            if role == 'STUDENT':
                carried_hours = {'demo_fms_advanced': 120, 'demo_fms_debt': 100}.get(username, 0)
                StudentProfile.objects.update_or_create(user=user, defaults={
                    'student_age': 24, 'student_phase': StudentProfile.FLYING,
                    'student_license_type': 'PPA', 'balance': Decimal('0'),
                    'flight_hours': Decimal(carried_hours), 'nav_flight_hours': Decimal('0'),
                    'flight_rate': Decimal('95') if username == 'demo_fms_advanced' else Decimal('130'),
                    'advanced_student': username == 'demo_fms_advanced',
                })
            elif role == 'INSTRUCTOR':
                InstructorProfile.objects.update_or_create(user=user, defaults={
                    'instructor_type': InstructorProfile.FLYING, 'instructor_license_type': 'PCA',
                    'flight_instructor_hourly_rate': Decimal('25'),
                })
            else:
                StaffProfile.objects.get_or_create(user=user, defaults={'position': 'Demo FMS'})
                user.user_permissions.add(*Permission.objects.filter(
                    content_type__app_label='accounts', codename__in=[
                        'can_manage_transactions', 'can_confirm_transactions', 'can_view_user_stats',
                    ],
                ))

    def create_aircraft(self):
        """Create isolated demo aircraft without changing the school's fleet."""
        self.planes = []
        for registration in AIRCRAFT:
            plane, _ = Aircraft.objects.update_or_create(registration=registration, defaults={
                'serial_number': registration, 'manufacturer': 'Piper', 'model': 'PA-28 DEMO',
                'year_manufactured': 2000, 'hourly_rate': Decimal('130'),
                'fuel_cost': Decimal('3.11'),
                'total_hours': Decimal('0'), 'notes': MARKER, 'is_active': True,
                'is_available': True, 'maintenance_status': 'OPERATIONAL',
            })
            self.planes.append(plane)
        for code in COURSES:
            CourseType.objects.get_or_create(code=code, defaults={'name': code})

    def timestamp(self, days_ago):
        """Return a stable noon timestamp relative to the scenario's end date."""
        return timezone.make_aware(datetime.combine(self.as_of - timedelta(days=days_ago), time(12)))

    def add_movement(self, student, amount, description, days_ago=40, credit=True, confirmed=True, category='N/A'):
        """Post a demo movement using StudentTransaction's normal balance update."""
        staff = self.users['demo_fms_staff']
        return StudentTransaction.objects.create(
            student_profile=StudentProfile.objects.get(user=student), amount=Decimal(amount),
            type=StudentTransaction.CREDIT if credit else StudentTransaction.DEBIT,
            category=category, notes=f'{MARKER} {description}', date_added=self.timestamp(days_ago).date(),
            added_by=staff, confirmed=confirmed, confirmed_by=staff if confirmed else None,
            confirmation_date=self.timestamp(days_ago) if confirmed else None,
        )

    def add_flight(self, student, stage, number, days_ago, hours='1.2', fuel='25.0'):
        """Validate and save a real flight form, including its accounting effects."""
        instructor = self.users['demo_fms_instructor']
        profile = StudentProfile.objects.get(user=student)
        plane = self.planes[number % 2]
        plane.refresh_from_db()
        form_class = (FlightEvaluation0_100Form, FlightEvaluation100_120Form, FlightEvaluation120_170Form)[stage]
        blank_form = form_class(user=instructor)
        session_choices = [value for value, _ in blank_form.fields['session_number'].choices if value != '']
        session_number = session_choices[(number - 1) % len(session_choices)]
        session_letter = 'A' if number > len(session_choices) else ''
        data = {}
        for name, field in blank_form.fields.items():
            if hasattr(field, 'choices') and name != 'aircraft':
                data[name] = next((str(value) for value, _ in field.choices if value != ''), '')
        initial = Decimal('100') + plane.total_hours
        data.update({
            'student_id': student.national_id, 'student_first_name': student.first_name,
            'student_last_name': student.last_name, 'student_license_type': 'PPA',
            'instructor_id': instructor.national_id, 'instructor_first_name': instructor.first_name,
            'instructor_last_name': instructor.last_name, 'instructor_license_type': 'PCA',
            'instructor_license_number': instructor.national_id, 'course_type': COURSES[stage],
            'flight_rules': 'IFR' if stage == 1 else 'VFR', 'solo_flight': 'NO',
            'session_number': session_number, 'session_letter': session_letter,
            'session_date': self.timestamp(days_ago).date().isoformat(),
            'accumulated_flight_hours': str(profile.flight_hours),
            'initial_hourmeter': str(initial), 'final_hourmeter': str(initial + Decimal(hours)),
            'fuel_consumed': fuel, 'aircraft': plane.pk, 'session_grade': 'S',
            'comments': f'{MARKER} Vuelo de demostración para revisar evaluación y contabilidad.',
            'discrepancy_type': '', 'discrepancy_description': '',
        })
        form = form_class(data=data, user=instructor)
        if not form.is_valid():
            raise CommandError(f'Demo flight validation failed: {form.errors.as_json()}')
        return form.save()

    def seed_scenarios(self):
        """Build pagination, fuel timing, pending payments and balance scenarios."""
        active = self.users['demo_fms_student']
        advanced = self.users['demo_fms_advanced']
        debt = self.users['demo_fms_debt']
        self.add_movement(active, '7000', 'Abono inicial confirmado')
        for index in range(28):
            flight = self.add_flight(active, 0, index + 1, 35 - index, fuel='0' if index >= 26 else '25')
            if index == 26:
                record_late_fuel(type(flight), flight.pk, Decimal('28'), self.users['demo_fms_staff'],
                                 observations=f'{MARKER} Combustible registrado días después del vuelo.',
                                 recorded_at=self.timestamp(3))
        self.add_movement(active, '50', 'Material de estudio', 7, credit=False, category=StudentTransaction.MATERIAL)
        self.add_movement(active, '20', 'Ajuste a favor del estudiante', 6)
        self.add_movement(active, '300', 'Transferencia pendiente de confirmar', 2, confirmed=False)
        self.add_movement(advanced, '1500', 'Abono para entrenamiento avanzado')
        for index in range(4):
            self.add_flight(advanced, 2, index + 1, 12 - index, hours='2.0', fuel='35')
        self.add_movement(debt, '100', 'Abono para cubrir parte del costo de los vuelos')
        for index in range(2):
            self.add_flight(debt, 1, index + 1, 5 - index, hours='1.5', fuel='25')

    def print_summary(self):
        """Print local login credentials and current scenario totals for UI checks."""
        self.stdout.write(f'Local demo password (initial / after --reset): {PASSWORD}')
        for username, _, role, _, _ in ACCOUNTS:
            user = User.objects.get(username=username)
            detail = role
            if role == 'STUDENT':
                profile = user.student_profile
                count = len(student_activity(profile)['movements'])
                detail = f'balance ${profile.balance:.2f}; total {profile.flight_hours} h; NAV {profile.nav_flight_hours} h; {count} movements'
            self.stdout.write(f'  {username}: {detail}')
        self.stdout.write('Aircraft: DEMO-FMS-01 / DEMO-FMS-02. The empty student has no activity.')
        self.stdout.write('Named YV204E/YV206E breakdowns are not populated by demo aircraft; overview totals include them.')
