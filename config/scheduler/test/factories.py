import factory
from django.contrib.auth import get_user_model
from scheduler.models import TrainingPeriod, FlightSlot, FlightRequest
from fleet.models import Aircraft
from accounts.models import StudentProfile
from datetime import date, timedelta

User = get_user_model()

class AircraftFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Aircraft

    manufacturer = factory.Faker('company')
    model = factory.Faker('word')
    registration = factory.Sequence(lambda n: f"YV{123 + n}E")
    serial_number = factory.Sequence(lambda n: f"SN{1000 + n}")
    year_manufactured = factory.Faker('year')
    is_active = True
    is_available = True

class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User
    
    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.Sequence(lambda n: f"user{n}@example.com")
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    national_id = factory.Sequence(lambda n: 1000000 + n)  # Valid range: 999999 < x < 100000000
    role = 'STUDENT'

class StudentProfileFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = StudentProfile
    
    user = factory.SubFactory(UserFactory)
    student_age = factory.Faker('random_int', min=16, max=100)
    balance = 1000.00

class TrainingPeriodFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = TrainingPeriod
    
    start_date = date.today()
    end_date = factory.LazyAttribute(lambda obj: obj.start_date + timedelta(days=6))
    is_active = False
    aircraft = factory.SubFactory(AircraftFactory)

class FlightSlotFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = FlightSlot
    
    training_period = factory.SubFactory(TrainingPeriodFactory)
    date = factory.LazyAttribute(lambda obj: obj.training_period.start_date)
    block = 'AM'
    aircraft = factory.LazyAttribute(lambda obj: obj.training_period.aircraft)
    status = 'available'

class FlightRequestFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = FlightRequest
    
    student = factory.SubFactory(UserFactory, role='STUDENT')
    slot = factory.SubFactory(FlightSlotFactory)
    status = 'pending'
    flexible = False
