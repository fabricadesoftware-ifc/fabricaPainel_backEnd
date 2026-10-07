from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from core.user.infra.user_django_app.models import Certificate, User


class AccessControlTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_user(
            email="admin.acl@test.local", password="password-123", name="Admin", user_type=User.ADMIN
        )
        self.student = User.objects.create_user(
            email="student.acl@test.local", password="password-123", name="Aluno", user_type=User.STUDENT
        )
        self.other_student = User.objects.create_user(
            email="other.acl@test.local", password="password-123", name="Outro", user_type=User.STUDENT
        )
        self.advisor = User.objects.create_user(
            email="advisor.acl@test.local",
            password="password-123",
            name="Orientador",
            user_type=User.TEACHER,
            is_advisor=True,
        )

    def test_anonymous_cannot_list_users(self):
        response = self.client.get("/api/users/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_student_cannot_edit_another_user(self):
        self.client.force_authenticate(user=self.student)
        response = self.client.patch(f"/api/users/{self.other_student.id}/", {"name": "Hackeado"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.other_student.refresh_from_db()
        self.assertEqual(self.other_student.name, "Outro")

    def test_student_cannot_create_admin_user(self):
        self.client.force_authenticate(user=self.student)
        response = self.client.post(
            "/api/users/",
            {"name": "Novo", "email": "novo.acl@test.local", "password": "x", "user_type": User.ADMIN},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_certificate_list_returns_only_own_certificates(self):
        own = Certificate.objects.create(user=self.student, work=self._work(), hash_validate="own-hash")
        other = Certificate.objects.create(user=self.other_student, work=self._work(), hash_validate="other-hash")

        self.client.force_authenticate(user=self.student)
        response = self.client.get("/api/certificates/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        hashes = [item["hash_validate"] for item in response.json()]
        self.assertIn(own.hash_validate, hashes)
        self.assertNotIn(other.hash_validate, hashes)

    def test_anonymous_cannot_list_certificates(self):
        response = self.client.get("/api/certificates/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_student_sees_only_related_users(self):
        work = self._work()
        work.team.team_members.add(self.student)
        self.client.force_authenticate(user=self.student)

        ids = {item["id"] for item in self.client.get("/api/users/").json()}

        self.assertIn(self.advisor.id, ids)
        self.assertIn(self.student.id, ids)
        self.assertNotIn(self.other_student.id, ids)

    def test_student_cannot_retrieve_unrelated_user(self):
        self.client.force_authenticate(user=self.student)
        response = self.client.get(f"/api/users/{self.other_student.id}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_student_registration_search_is_exact_match_only(self):
        self.other_student.registration = 123456
        self.other_student.save()
        self.client.force_authenticate(user=self.student)

        partial = self.client.get("/api/users/", {"type": "STUDENT", "registration": "1234"}).json()
        exact = self.client.get("/api/users/", {"type": "STUDENT", "registration": "123456"}).json()

        self.assertNotIn(self.other_student.id, {item["id"] for item in partial})
        self.assertIn(self.other_student.id, {item["id"] for item in exact})

    def _work(self):
        from core.edition.infra.edition_django_app.models import Edition
        from core.work.infra.work_django_app.models import Work

        edition = Edition.objects.filter(year=2026).first()
        if edition is None:
            edition = Edition.objects.create(year=2026, edition_name="Teste", theme="Teste", workload=40)
        from core.cross_cutting_themes.infra.cross_cutting_themes_django_app.models import CrossCuttingTheme

        from core.work.infra.work_django_app.models import Team

        theme, _ = CrossCuttingTheme.objects.get_or_create(name="Tema ACL")
        team = Team.objects.create(edition=edition)
        return Work.objects.create(
            title="Trabalho ACL",
            abstract="x",
            edition=edition,
            cross_cutting_theme=theme,
            team=team,
            advisor=self.advisor,
        )
