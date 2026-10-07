from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from core.cross_cutting_themes.infra.cross_cutting_themes_django_app.models import CrossCuttingTheme
from core.edition.infra.edition_django_app.models import Edition
from core.user.infra.user_django_app.models import User
from core.work.domain.value_objects import WorkAdvisorStatusType, WorkStatusType
from core.work.infra.work_django_app.models import Team, Work


class AdvisorSwitchTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.edition = Edition.objects.create(year=2026, edition_name="Teste", theme="Teste", workload=40)
        self.student = User.objects.create_user(
            email="student.switch@test.local", password="password-123", name="Aluno", user_type=User.STUDENT
        )
        self.first_advisor = User.objects.create_user(
            email="advisor1.switch@test.local",
            password="password-123",
            name="Orientador 1",
            user_type=User.TEACHER,
            is_advisor=True,
        )
        self.second_advisor = User.objects.create_user(
            email="advisor2.switch@test.local",
            password="password-123",
            name="Orientador 2",
            user_type=User.TEACHER,
            is_advisor=True,
        )
        theme = CrossCuttingTheme.objects.create(name="Tema Switch")
        self.team = Team.objects.create(edition=self.edition)
        self.team.team_members.add(self.student)
        self.work = Work.objects.create(
            title="Trabalho Switch",
            abstract="Resumo original",
            edition=self.edition,
            cross_cutting_theme=theme,
            team=self.team,
            advisor=self.first_advisor,
            status=WorkStatusType.Type.PENDING.value,
            advisor_status=WorkAdvisorStatusType.Type.REJECTED.value,
        )
        self.client.force_authenticate(user=self.student)

    def test_switching_advisor_after_rejection_reopens_decision(self):
        response = self.client.patch(f"/api/work/{self.work.id}/", {"advisor": self.second_advisor.id}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.work.refresh_from_db()
        self.assertEqual(self.work.advisor_id, self.second_advisor.id)
        self.assertEqual(self.work.advisor_status, WorkAdvisorStatusType.Type.PENDING.value)

    def test_cannot_pick_same_advisor_who_rejected(self):
        response = self.client.patch(f"/api/work/{self.work.id}/", {"advisor": self.first_advisor.id}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.work.refresh_from_db()
        self.assertEqual(self.work.advisor_id, self.first_advisor.id)

    def test_abstract_only_patch_still_saves(self):
        response = self.client.patch(f"/api/work/{self.work.id}/", {"abstract": "Resumo novo"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.work.refresh_from_db()
        self.assertEqual(self.work.abstract, "Resumo novo")
