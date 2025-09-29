from django.test import TestCase

# Import all test classes to make them discoverable
from .test.test_model_flight_period import FlightPeriodModelTest
from .test.test_model_flight_slot import FlightSlotModelTest
from .test.test_model_flight_request import FlightRequestModelTest
from .test.test_views import FlightRequestViewTest, FlightPeriodViewTest, ChangeSlotStatusViewTest
from .test.test_forms import CreateFlightPeriodFormTest