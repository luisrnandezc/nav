import factory
from django.contrib.auth import get_user_model
from accounts.models import StudentProfile

User = get_user_model()


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f"fms_user{n}")
    email = factory.Sequence(lambda n: f"fms_user{n}@example.com")
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    national_id = factory.Sequence(lambda n: 2000000 + n)
    role = 'STUDENT'


class StudentProfileFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = StudentProfile

    user = factory.SubFactory(UserFactory)
    student_age = factory.Faker('random_int', min=16, max=50)
    sim_hours = 0.0
    flight_hours = 0.0
    nav_flight_hours = 0.0
    balance = 1000.00
