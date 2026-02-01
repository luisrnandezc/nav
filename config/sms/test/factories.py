import factory
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from accounts.models import StudentProfile
from sms.models import VoluntaryHazardReport, Risk, MitigationAction

User = get_user_model()


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f"sms_user{n}")
    email = factory.Sequence(lambda n: f"sms_user{n}@example.com")
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    national_id = factory.Sequence(lambda n: 2000000 + n)
    role = 'STUDENT'


class StaffUserFactory(UserFactory):
    role = 'STAFF'


class InstructorUserFactory(UserFactory):
    role = 'INSTRUCTOR'


class StudentProfileFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = StudentProfile

    user = factory.SubFactory(UserFactory)
    student_age = factory.Faker('random_int', min=16, max=50)
    sim_hours = 0.0
    flight_hours = 0.0
    nav_flight_hours = 0.0
    balance = 1000.00


class VoluntaryHazardReportFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = VoluntaryHazardReport

    description = factory.Faker('paragraph', nb_sentences=3)
    area = 'OPERATIONS'
    date = factory.LazyFunction(timezone.now)
    time = factory.LazyFunction(timezone.localtime)
    is_valid = False
    is_registered = False
    is_processed = False
    is_resolved = False
    ai_analysis_status = 'PENDING'


class RiskFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Risk

    report = factory.SubFactory(VoluntaryHazardReportFactory)
    description = factory.Faker('sentence')
    status = 'NOT_EVALUATED'
    condition = 'UNMITIGATED'
    pre_evaluation_severity = '0'
    pre_evaluation_probability = '0'
    post_evaluation_severity = '0'
    post_evaluation_probability = '0'


class MitigationActionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = MitigationAction

    risk = factory.SubFactory(RiskFactory)
    description = factory.Faker('sentence')
    status = 'PENDING'
    due_date = factory.LazyFunction(lambda: timezone.now().date() + timedelta(days=15))
    follow_date = factory.LazyFunction(lambda: timezone.now().date() + timedelta(days=7))
