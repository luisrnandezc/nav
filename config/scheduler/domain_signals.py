from django.dispatch import Signal

# Values for ``cancelled_by`` on ``flight_request_cancelled`` (who cancelled).
FLIGHT_REQUEST_CANCELLED_BY_STUDENT = "student"
FLIGHT_REQUEST_CANCELLED_BY_STAFF = "staff"

# Fired after a flight request is cancelled. Send kwargs: instance=FlightRequest,
# cancelled_by=FLIGHT_REQUEST_CANCELLED_BY_STUDENT or FLIGHT_REQUEST_CANCELLED_BY_STAFF.
flight_request_cancelled = Signal()

# Sent when an instructor is assigned to a slot. Provides: slot, instructor
instructor_assigned_to_slot = Signal()

# Sent when an instructor is removed from a slot. Provides: slot, instructor
instructor_removed_from_slot = Signal()
