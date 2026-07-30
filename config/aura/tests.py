from django.test import TestCase
from django.urls import reverse

from accounts.models import InstructorProfile, StaffProfile, StudentProfile, User


class AuraAccessTests(TestCase):
    def setUp(self):
        self.flying_student = self.create_student(
            "flying-one",
            2000001,
            StudentProfile.FLYING,
        )
        self.other_flying_student = self.create_student(
            "flying-two",
            2000002,
            StudentProfile.FLYING,
        )
        self.ground_student = self.create_student(
            "ground",
            2000003,
            StudentProfile.GROUND,
        )

        self.instructor = self.create_user(
            "instructor",
            User.Role.INSTRUCTOR,
            2000004,
        )
        InstructorProfile.objects.create(user=self.instructor)

        self.staff = self.create_user("staff", User.Role.STAFF, 2000005)
        StaffProfile.objects.create(user=self.staff)

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

    def create_student(self, username, national_id, phase):
        user = self.create_user(username, User.Role.STUDENT, national_id)
        StudentProfile.objects.create(
            user=user,
            student_age=20,
            student_phase=phase,
        )
        return user

    def activate_role(self, user, role):
        self.client.force_login(user)
        session = self.client.session
        session["selected_role"] = role
        session.save()

    def test_instructor_dashboard_lists_only_flying_students(self):
        self.activate_role(self.instructor, "INSTRUCTOR")

        response = self.client.get(reverse("aura:student_review_list"))

        self.assertEqual(response.status_code, 200)
        listed_users = {profile.user for profile in response.context["students"]}
        self.assertSetEqual(
            listed_users,
            {self.flying_student, self.other_flying_student},
        )
        self.assertNotIn(self.ground_student, listed_users)

    def test_staff_dashboard_lists_only_flying_students(self):
        self.activate_role(self.staff, "STAFF")

        response = self.client.get(reverse("aura:student_review_list"))

        self.assertEqual(response.status_code, 200)
        listed_users = {profile.user for profile in response.context["students"]}
        self.assertSetEqual(
            listed_users,
            {self.flying_student, self.other_flying_student},
        )

    def test_dashboard_searches_flying_students_by_name(self):
        self.activate_role(self.instructor, "INSTRUCTOR")

        response = self.client.get(
            reverse("aura:student_review_list"),
            {"q": "Two"},
        )

        self.assertEqual(response.status_code, 200)
        listed_users = [profile.user for profile in response.context["students"]]
        self.assertEqual(listed_users, [self.other_flying_student])
        self.assertEqual(response.context["search_term"], "Two")

    def test_dashboard_searches_flying_students_by_national_id(self):
        self.activate_role(self.instructor, "INSTRUCTOR")

        response = self.client.get(
            reverse("aura:student_review_list"),
            {"q": str(self.flying_student.national_id)},
        )

        self.assertEqual(response.status_code, 200)
        listed_users = [profile.user for profile in response.context["students"]]
        self.assertEqual(listed_users, [self.flying_student])

    def test_dashboard_search_never_returns_ground_students(self):
        self.activate_role(self.instructor, "INSTRUCTOR")

        response = self.client.get(
            reverse("aura:student_review_list"),
            {"q": "Ground"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["students"].exists())

    def test_instructor_can_view_each_flying_students_analysis(self):
        self.activate_role(self.instructor, "INSTRUCTOR")

        for student in (self.flying_student, self.other_flying_student):
            with self.subTest(student=student.username):
                response = self.client.get(
                    reverse(
                        "aura:student_global_review",
                        args=[student.student_profile.id],
                    )
                )
                self.assertEqual(response.status_code, 200)

    def test_flying_student_home_redirects_to_personal_analysis(self):
        self.activate_role(self.flying_student, "STUDENT")

        response = self.client.get(reverse("aura:home"))

        self.assertRedirects(
            response,
            reverse("aura:my_global_review"),
            fetch_redirect_response=False,
        )

    def test_flying_student_can_view_personal_analysis(self):
        self.activate_role(self.flying_student, "STUDENT")

        response = self.client.get(reverse("aura:my_global_review"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["student_profile"],
            self.flying_student.student_profile,
        )

    def test_student_cannot_view_another_students_analysis(self):
        self.activate_role(self.flying_student, "STUDENT")

        response = self.client.get(
            reverse(
                "aura:student_global_review",
                args=[self.other_flying_student.student_profile.id],
            )
        )

        self.assertRedirects(
            response,
            reverse("dashboard:dashboard"),
            fetch_redirect_response=False,
        )

    def test_ground_student_cannot_access_aura(self):
        self.activate_role(self.ground_student, "STUDENT")

        response = self.client.get(reverse("aura:home"))

        self.assertRedirects(
            response,
            reverse("dashboard:dashboard"),
            fetch_redirect_response=False,
        )
