from django.test import TestCase
from django.contrib.auth import get_user_model
from decimal import Decimal
from django.utils import timezone

from fleet.models import Simulator
from .factories import UserFactory, StudentProfileFactory
from ..forms import SimEvaluationForm
from accounts.models import InstructorProfile


User = get_user_model()


class SimEvaluationModelTest(TestCase):
	"""Tests for SimEvaluation form behavior related to student balance."""

	def setUp(self):
		"""Set up a student, their profile, an instructor and an active simulator."""
		# Create test users and profile using shared factories
		self.student = UserFactory()
		# Override profile values
		self.student_profile = StudentProfileFactory(user=self.student, balance=Decimal('1000.00'), sim_hours=Decimal('5.0'))

		# Create an instructor user
		self.instructor = UserFactory(role='INSTRUCTOR')
		# Ensure instructor_profile exists because the form expects it
		InstructorProfile.objects.create(user=self.instructor)

		# Create an active simulator
		self.simulator = Simulator.objects.create(name='FPT', is_active=True, is_available=True)

	def test_sim_evaluation_does_not_change_student_balance(self):
		"""Creating and deleting a SimEvaluation must not modify student `balance`."""
		initial_balance = Decimal(self.student_profile.balance)

		# Prepare valid form data
		long_comment = 'C' * 80
		form_data = {
			'instructor_id': self.instructor.national_id,
			'instructor_first_name': self.instructor.first_name,
			'instructor_last_name': self.instructor.last_name,
			'instructor_license_type': 'PCA',
			'instructor_license_number': self.instructor.national_id,
			'student_id': self.student.national_id,
			'student_first_name': self.student.first_name,
			'student_last_name': self.student.last_name,
			'student_license_type': 'AP',
			'student_license_number': self.student.national_id,
			'course_type': 'PPA-P',
			'session_date': timezone.now().date(),
			'accumulated_sim_hours': self.student_profile.sim_hours,
			'session_sim_hours': Decimal('1.0'),
			'simulator': self.simulator.id,
			'session_type': 'Simple',
			'session_grade': 'S',
			'comments': long_comment,
		}

		form = SimEvaluationForm(data=form_data, user=self.instructor)
		# Fill any remaining required fields by inspecting the form's fields
		probe = SimEvaluationForm(user=self.instructor)
		for name, field in probe.fields.items():
			if name in form_data:
				continue
			if not getattr(field, 'required', False):
				continue
			# Choice fields: pick the first non-empty choice
			from django import forms as django_forms
			if isinstance(field, django_forms.ChoiceField):
				choice_val = None
				for val, _label in getattr(field, 'choices', []):
					if val not in (None, '',):
						choice_val = val
						break
				# fallback to first choice
				if choice_val is None and field.choices:
					choice_val = field.choices[0][0]
				form_data[name] = choice_val
			elif isinstance(field, django_forms.DecimalField) or isinstance(field, django_forms.FloatField):
				form_data[name] = '0.0'
			elif isinstance(field, django_forms.IntegerField):
				form_data[name] = 0
			elif isinstance(field, django_forms.DateField):
				form_data[name] = timezone.now().date()
			else:
				# Default to a short non-empty string; comments already provided
				form_data[name] = 'OK'

		form = SimEvaluationForm(data=form_data, user=self.instructor)
		self.assertTrue(form.is_valid(), msg=form.errors.as_json())

		evaluation = form.save()

		# Balance should remain unchanged after creation
		self.student_profile.refresh_from_db()
		self.assertEqual(self.student_profile.balance, initial_balance)

		# Deleting the evaluation must also not affect balance
		evaluation.delete()
		self.student_profile.refresh_from_db()
		self.assertEqual(self.student_profile.balance, initial_balance)

