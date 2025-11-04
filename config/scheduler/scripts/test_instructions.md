# Testing cancel_overdue_requests.py

## Method 1: Using Helper Script (Recommended)

1. **Create test data:**
   ```bash
   cd config/scheduler/scripts
   python create_test_overdue_requests.py
   ```

2. **Run the script:**
   ```bash
   python cancel_overdue_requests.py
   ```

3. **Verify results:**
   - Check console output for cancellation messages
   - Use Django shell or admin to verify status changed

## Method 2: Using Django Shell

1. **Open Django shell:**
   ```bash
   cd config
   python manage.py shell
   ```

2. **Create test data in shell:**
   ```python
   from django.utils.timezone import localdate
   from datetime import timedelta
   from scheduler.models import FlightRequest, FlightSlot, FlightPeriod
   from fleet.models import Aircraft
   from accounts.models import StudentProfile, User
   from django.contrib.auth import get_user_model
   
   User = get_user_model()
   today = localdate()
   
   # Create or get aircraft
   aircraft, _ = Aircraft.objects.get_or_create(
       registration="TEST001",
       defaults={'manufacturer': 'Test', 'model': 'Test', 
                'serial_number': 'TEST', 'year_manufactured': 2020,
                'is_active': True, 'is_available': True, 'hourly_rate': 100.00}
   )
   
   # Create or get student
   student, _ = User.objects.get_or_create(
       username='test_student',
       defaults={'email': 'test@example.com', 'role': 'STUDENT', 
                'national_id': 12345678}
   )
   
   StudentProfile.objects.get_or_create(user=student, defaults={'balance': 1000.00})
   
   # Create period
   period, _ = FlightPeriod.objects.get_or_create(
       aircraft=aircraft,
       start_date=today - timedelta(days=14),
       end_date=today - timedelta(days=8),
       defaults={'is_active': True}
   )
   
   # Create overdue slot and request
   overdue_slot, _ = FlightSlot.objects.get_or_create(
       flight_period=period,
       date=today - timedelta(days=1),  # Yesterday (overdue)
       block='AM',
       defaults={'aircraft': aircraft, 'status': 'pending', 'student': student}
   )
   
   overdue_request, _ = FlightRequest.objects.get_or_create(
       student=student,
       slot=overdue_slot,
       defaults={'status': 'pending'}
   )
   
   print(f"Created overdue request ID: {overdue_request.id}")
   ```

3. **Exit shell and run script:**
   ```bash
   exit
   cd scheduler/scripts
   python cancel_overdue_requests.py
   ```

## Method 3: Using Django Admin

1. Go to Django admin: http://localhost:8000/admin
2. Manually create:
   - An Aircraft
   - A FlightPeriod (with date in the past)
   - A FlightSlot (with date before today)
   - A FlightRequest (status='pending') for that slot
3. Run the script: `python cancel_overdue_requests.py`
4. Check admin to see status changed to 'cancelled'

## Method 4: Check Before/After Counts

```python
# In Django shell, before running script:
from scheduler.models import FlightRequest
from django.utils.timezone import localdate

today = localdate()
overdue_count = FlightRequest.objects.filter(
    status='pending',
    slot__date__lt=today
).count()
print(f"Overdue pending requests: {overdue_count}")

# After running script:
overdue_count_after = FlightRequest.objects.filter(
    status='pending',
    slot__date__lt=today
).count()
print(f"Overdue pending requests after: {overdue_count_after}")  # Should be 0

cancelled_count = FlightRequest.objects.filter(
    status='cancelled',
    slot__date__lt=today
).count()
print(f"Cancelled overdue requests: {cancelled_count}")
```

