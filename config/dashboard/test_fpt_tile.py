from django.contrib.auth.models import Permission
from django.test import RequestFactory, TestCase
from django.urls import reverse

from accounts.models import InstructorProfile, StaffProfile, StudentProfile
from dashboard.views import _build_launchpad_apps
from scheduler.test.factories import UserFactory


class FPTTileTests(TestCase):
    def apps(self, user, role, profile):
        request = RequestFactory().get('/')
        request.user = user
        return _build_launchpad_apps(request, role, profile)

    def test_staff_and_instructor_tile_requires_view_or_manage_permission(self):
        for role, profile_class in [('STAFF', StaffProfile), ('INSTRUCTOR', InstructorProfile)]:
            for permission in (None, 'view_fpt_schedule', 'manage_fpt_schedule'):
                with self.subTest(role=role, permission=permission):
                    user = UserFactory(role=role)
                    profile = profile_class.objects.create(user=user)
                    if permission:
                        user.user_permissions.add(Permission.objects.get(codename=permission))
                    tiles = [tile for tile in self.apps(user, role, profile) if tile['key'] == 'fpt_scheduler']
                    self.assertEqual(bool(tiles), bool(permission))
                    if tiles:
                        self.assertEqual(tiles[0]['url'], reverse('scheduler:fpt_calendar'))

    def test_students_do_not_get_tile_even_with_permissions(self):
        user = UserFactory(role='STUDENT')
        user.user_permissions.add(Permission.objects.get(codename='manage_fpt_schedule'))
        profile = StudentProfile.objects.create(user=user, student_age=20)
        self.assertNotIn('fpt_scheduler', [tile['key'] for tile in self.apps(user, 'STUDENT', profile)])

    def test_staff_using_student_dashboard_does_not_get_tile(self):
        user = UserFactory(role='STAFF')
        user.user_permissions.add(Permission.objects.get(codename='view_fpt_schedule'))
        profile = StudentProfile.objects.create(user=user, student_age=20)
        self.assertNotIn('fpt_scheduler', [tile['key'] for tile in self.apps(user, 'STUDENT', profile)])
