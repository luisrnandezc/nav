"""Read-only reconciliation report for one student's stored balance."""
from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError

from accounts.models import StudentProfile, User
from transactions.student_activity import student_activity


ZERO = Decimal('0')


class Command(BaseCommand):
    help = 'Audit one student balance against retained flights and transactions without writing data.'

    def add_arguments(self, parser):
        """Accept the student's national ID and an optional movement listing."""
        parser.add_argument('national_id', type=int)
        parser.add_argument(
            '--details',
            action='store_true',
            help='Print every reconstructed flight and transaction movement.',
        )

    def handle(self, *args, **options):
        """Print stored and reconstructed balances without changing any model."""
        try:
            profile = StudentProfile.objects.select_related('user').get(
                user__national_id=options['national_id'],
                user__role=User.Role.STUDENT,
            )
        except StudentProfile.DoesNotExist as exc:
            raise CommandError(
                f'No student profile found for national ID {options["national_id"]}.'
            ) from exc

        activity = student_activity(profile)
        movements = activity['movements']
        applied = [movement for movement in movements if not movement['pending']]
        pending = [movement for movement in movements if movement['pending']]
        automatic = [movement for movement in applied if movement['id'].startswith('flight-')]
        transactions = [
            movement for movement in applied if movement['id'].startswith('transaction-')
        ]

        automatic_debits = sum((movement['amount'] for movement in automatic), ZERO)
        transaction_credits = sum((
            movement['amount'] for movement in transactions if movement['credit']
        ), ZERO)
        transaction_debits = sum((
            movement['amount'] for movement in transactions if not movement['credit']
        ), ZERO)
        pending_credits = sum((
            movement['amount'] for movement in pending if movement['credit']
        ), ZERO)
        pending_debits = sum((
            movement['amount'] for movement in pending if not movement['credit']
        ), ZERO)
        reconstructed = transaction_credits - transaction_debits - automatic_debits
        difference = profile.balance - reconstructed

        self.stdout.write(f'Student: {profile.user.get_full_name()} ({profile.user.national_id})')
        self.stdout.write(f'Username: {profile.user.username}')
        self.stdout.write(f'Stored balance: ${profile.balance:.2f}')
        self.stdout.write('')
        self.stdout.write('Applied movements retained in the database:')
        self.stdout.write(
            f'  Automatic flight debits: {len(automatic)} / ${automatic_debits:.2f}'
        )
        self.stdout.write(
            f'  Confirmed transaction credits: '
            f'{sum(1 for movement in transactions if movement["credit"])} / '
            f'${transaction_credits:.2f}'
        )
        self.stdout.write(
            f'  Confirmed transaction debits: '
            f'{sum(1 for movement in transactions if not movement["credit"])} / '
            f'${transaction_debits:.2f}'
        )
        self.stdout.write(f'Reconstructed balance (zero opening balance): ${reconstructed:.2f}')
        self.stdout.write(f'Unexplained/opening difference: ${difference:.2f}')
        self.stdout.write('')
        self.stdout.write(
            f'Pending credits (excluded): {sum(1 for movement in pending if movement["credit"])} '
            f'/ ${pending_credits:.2f}'
        )
        self.stdout.write(
            f'Pending debits (excluded): {sum(1 for movement in pending if not movement["credit"])} '
            f'/ ${pending_debits:.2f}'
        )
        self.stdout.write(f'Unlinked historical fuel present: {activity["unresolved_fuel"]}')

        if options['details']:
            self.stdout.write('')
            self.stdout.write('Movements (newest first):')
            for movement in movements:
                status = 'PENDING' if movement['pending'] else 'APPLIED'
                direction = 'CREDIT' if movement['credit'] else 'DEBIT'
                self.stdout.write(
                    f'  {movement["date"]:%Y-%m-%d} | {status:7} | {direction:6} | '
                    f'${movement["amount"]:.2f} | {movement["id"]} | {movement["title"]}'
                )

        if difference:
            self.stdout.write('')
            self.stdout.write(self.style.WARNING(
                'The difference can represent an opening balance, deleted/missing historical '
                'records, or a balance changed outside the retained accounting flows.'
            ))
        else:
            self.stdout.write(self.style.SUCCESS('Stored balance matches retained movements.'))
