from django.dispatch import Signal

# Sent when a FlightRequest is cancelled. Provides: instance
flight_request_cancelled = Signal()

# Sent when an instructor is assigned to a slot. Provides: slot, instructor
instructor_assigned_to_slot = Signal()

# Sent when an instructor is removed from a slot. Provides: slot, instructor
instructor_removed_from_slot = Signal()


