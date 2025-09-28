class FlightPeriodError(Exception):
    """Base exception for flight period related errors."""
    pass

class FlightRequestError(Exception):
    """Base exception for flight request related errors."""
    pass

class PeriodNotActiveError(FlightRequestError):
    """Raised when trying to create request for inactive period."""
    pass

class InsufficientBalanceError(FlightRequestError):
    """Raised when student has insufficient balance."""
    pass

class SlotNotAvailableError(FlightRequestError):
    """Raised when slot is not available for booking."""
    pass

class MaxRequestsExceededError(FlightRequestError):
    """Raised when student has exceeded the maximum number of requests."""
    pass

class PeriodOverlapError(FlightPeriodError):
    """Raised when periods overlap."""
    pass

class InvalidPeriodDurationError(FlightPeriodError):
    """Raised when period duration is invalid."""
    pass

class AircraftNotAvailableError(FlightPeriodError):
    """Raised when aircraft is not available."""
    pass