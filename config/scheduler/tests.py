from django.test import TestCase

# Import all test classes to make them discoverable
from .test.test_models import FlightRequestModelTest, FlightPeriodModelTest
from .test.test_views import FlightRequestViewTest, FlightPeriodViewTest, ChangeSlotStatusViewTest
from .test.test_forms import CreateFlightPeriodFormTest