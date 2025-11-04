#!/usr/bin/env python
"""
Helper script to create test data for testing cancel_overdue_requests.py
Run this first to create some overdue pending requests, then run cancel_overdue_requests.py
"""
import os
import sys
import django
from django.utils.timezone import localdate
from datetime import timedelta

project_dir = os.path.dirname(os.path.abspath(__file__))
django_dir = os.path.join(project_dir, '..', '..')
sys.path.insert(0, django_dir)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from scheduler.models import FlightRequest, FlightSlot, FlightPeriod
from fleet.models import Aircraft
from accounts.models import StudentProfile, User
from django.contrib.auth import get_user_model

User = get_user_model()

def create_test_data():
    """Create test data: overdue pending requests and some non-overdue ones."""
    
    aircraft, _ = Aircraft.objects.get_or_create(
        registration="TEST001",
        defaults={
            'manufacturer': 'Test',
            'model': 'Test Model',
            'serial_number': 'TEST123',
            'year_manufactured': 2020,
            'is_active': True,
            'is_available': True,
            'hourly_rate': 100.00
        }
    )
    
    student, _ = User.objects.get_or_create(
        username='test_student',
        defaults={
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'Student',
            'role': 'STUDENT',
            'national_id': 12345678
        }
    )
    
    profile, _ = StudentProfile.objects.get_or_create(
        user=student,
        defaults={
            'balance': 1500.00,
            'student_age': 25
        }
    )
    if profile.balance != 1500.00:
        profile.balance = 1500.00
        profile.save()
    
    existing_requests = FlightRequest.objects.filter(student=student)
    if existing_requests.exists():
        print(f"Cleaning up {existing_requests.count()} existing test requests...")
        for req in existing_requests:
            req.delete()
    
    FlightSlot.objects.filter(student=student).update(status='available', student=None)
    
    today = localdate()
    period, _ = FlightPeriod.objects.get_or_create(
        aircraft=aircraft,
        start_date=today - timedelta(days=14),
        end_date=today - timedelta(days=8),
        defaults={'is_active': True}
    )
    
    yesterday = today - timedelta(days=1)
    two_days_ago = today - timedelta(days=2)
    tomorrow = today + timedelta(days=1)
    
    FlightRequest.objects.filter(
        slot__flight_period=period,
        slot__date__in=[yesterday, two_days_ago, tomorrow]
    ).delete()
    
    overdue_slot, _ = FlightSlot.objects.get_or_create(
        flight_period=period,
        date=yesterday,
        block='AM',
        defaults={
            'aircraft': aircraft,
            'status': 'available',
            'student': None
        }
    )
    overdue_slot.status = 'available'
    overdue_slot.student = None
    overdue_slot.save()
    
    overdue_slot2, _ = FlightSlot.objects.get_or_create(
        flight_period=period,
        date=two_days_ago,
        block='PM',
        defaults={
            'aircraft': aircraft,
            'status': 'available',
            'student': None
        }
    )
    overdue_slot2.status = 'available'
    overdue_slot2.student = None
    overdue_slot2.save()
    
    future_slot, _ = FlightSlot.objects.get_or_create(
        flight_period=period,
        date=tomorrow,
        block='AM',
        defaults={
            'aircraft': aircraft,
            'status': 'available',
            'student': None
        }
    )
    future_slot.status = 'available'
    future_slot.student = None
    future_slot.save()
    
    FlightRequest.objects.filter(student=student, slot=overdue_slot).delete()
    FlightRequest.objects.filter(student=student, slot=overdue_slot2).delete()
    FlightRequest.objects.filter(student=student, slot=future_slot).delete()
    
    profile.refresh_from_db()
    
    current_count = FlightRequest.objects.filter(
        student=student, 
        status__in=['pending', 'approved']
    ).count()
    print(f"Current pending/approved requests for student: {current_count}")
    print(f"Student balance: ${profile.balance}, Max allowed: {int(profile.balance // 500)}")
    
    overdue_request1 = FlightRequest.objects.create(
        student=student,
        slot=overdue_slot,
        status='pending'
    )
    print(f"Created request 1: ID {overdue_request1.id}")
    
    overdue_request2 = FlightRequest.objects.create(
        student=student,
        slot=overdue_slot2,
        status='pending'
    )
    print(f"Created request 2: ID {overdue_request2.id}")
    
    future_request = FlightRequest.objects.create(
        student=student,
        slot=future_slot,
        status='pending'
    )
    print(f"Created request 3: ID {future_request.id}")
    
    print(f"Created test data:")
    print(f"  - Overdue pending request 1: ID {overdue_request1.id} (date: {overdue_slot.date})")
    print(f"  - Overdue pending request 2: ID {overdue_request2.id} (date: {overdue_slot2.date})")
    print(f"  - Future pending request: ID {future_request.id} (date: {future_slot.date})")
    print(f"\nToday is: {today}")
    print(f"\nNow run: python cancel_overdue_requests.py")

if __name__ == "__main__":
    create_test_data()

