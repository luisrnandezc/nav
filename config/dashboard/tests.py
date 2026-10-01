from django.contrib.auth.models import Permission
from django.test import RequestFactory, TestCase

from accounts.models import InstructorProfile, StaffProfile, StudentProfile, User
from dashboard.views import _build_launchpad_apps


class AuraLaunchpadVisibilityTests(TestCase):
    def setUp(self):
        self.request_factory = RequestFactory()

    def create_user(self, username, role, national_id):
        return User.objects.create_user(
            username=username,
            email=f"{username}@example.com",
            national_id=national_id,
            password="test-password",
            role=role,
            first_name=username.title(),
            last_name="Test",
        )

    def aura_is_visible(self, user, active_role, profile):
        request = self.request_factory.get("/")
        request.user = user
        apps = _build_launchpad_apps(request, active_role, profile)
        return any(app["key"] == "aura" for app in apps)

    def launchpad_keys(self, user, active_role, profile):
        request = self.request_factory.get("/")
        request.user = user
        return {app["key"] for app in _build_launchpad_apps(request, active_role, profile)}

    def test_staff_can_see_aura_tile(self):
        user = self.create_user("staff", User.Role.STAFF, 1000001)
        profile = StaffProfile.objects.create(user=user)

        self.assertTrue(self.aura_is_visible(user, "STAFF", profile))

    def test_instructor_can_see_aura_tile(self):
        user = self.create_user("instructor", User.Role.INSTRUCTOR, 1000002)
        profile = InstructorProfile.objects.create(user=user)

        self.assertTrue(self.aura_is_visible(user, "INSTRUCTOR", profile))

    def test_flying_student_can_see_aura_tile(self):
        user = self.create_user("flying", User.Role.STUDENT, 1000003)
        profile = StudentProfile.objects.create(
            user=user,
            student_age=20,
            student_phase=StudentProfile.FLYING,
        )

        self.assertTrue(self.aura_is_visible(user, "STUDENT", profile))

    def test_ground_student_cannot_see_aura_tile(self):
        user = self.create_user("ground", User.Role.STUDENT, 1000004)
        profile = StudentProfile.objects.create(
            user=user,
            student_age=20,
            student_phase=StudentProfile.GROUND,
        )

        self.assertFalse(self.aura_is_visible(user, "STUDENT", profile))

    def test_student_activity_tile_is_only_visible_to_permitted_staff(self):
        student = self.create_user("activity_student", User.Role.STUDENT, 1000005)
        student_profile = StudentProfile.objects.create(user=student, student_age=20)
        self.assertNotIn(
            "student_balance_stats",
            self.launchpad_keys(student, "STUDENT", student_profile),
        )

        staff = self.create_user("activity_staff", User.Role.STAFF, 1000006)
        staff_profile = StaffProfile.objects.create(user=staff)
        self.assertNotIn(
            "student_balance_stats",
            self.launchpad_keys(staff, "STAFF", staff_profile),
        )
        staff.user_permissions.add(Permission.objects.get(codename="can_manage_transactions"))
        staff = User.objects.get(pk=staff.pk)
        self.assertIn(
            "student_balance_stats",
            self.launchpad_keys(staff, "STAFF", staff_profile),
        )
