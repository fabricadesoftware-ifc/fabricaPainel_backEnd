from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient, APITransactionTestCase

from core.assessment.infra.assessment_django_app.models import Assessment, StudentAssessments
from core.cross_cutting_themes.infra.cross_cutting_themes_django_app.models import CrossCuttingTheme
from core.edition.infra.edition_django_app.models import Edition
from core.field.infra.field_django_app.models import Field
from core.user.domain.value_objects import UserType
from core.user.infra.user_django_app.models import Class, Evaluator, User, UserClass
from core.work.domain.value_objects import (
    WorkAdvisorStatusType,
    WorkCollaboratorStatusType,
    WorkStatusType,
)
from core.work.infra.work_django_app.models import Ods, Team, Work, WorkCollaborator


class EditionFlowTestCase(APITransactionTestCase):
    reset_sequences = True

    def setUp(self):
        self.client = APIClient()
        self.today = timezone.localdate()
        self.password = "test-password-123"
        self.registration = 1000

        self.field = Field.objects.create(name="Informatica")
        self.theme = CrossCuttingTheme.objects.create(name="Sustentabilidade")
        self.ods = Ods.objects.create(name="ODS 4 - Educacao de Qualidade")
        self.class_name = Class.objects.create(name="1INFO1")

        self.student = self.create_user("student@test.local", UserType.Type.STUDENT.value)
        self.student_two = self.create_user("student2@test.local", UserType.Type.STUDENT.value)
        self.advisor = self.create_user(
            "advisor@test.local",
            UserType.Type.TEACHER.value,
            is_advisor=True,
        )
        self.collaborator = self.create_user(
            "collaborator@test.local",
            UserType.Type.TEACHER.value,
            is_collaborator=True,
        )
        self.evaluator_user = self.create_user(
            "evaluator@test.local",
            UserType.Type.TEACHER.value,
        )
        self.evaluator = Evaluator.objects.create(user=self.evaluator_user)

        for student in [self.student, self.student_two]:
            UserClass.objects.create(
                user=student,
                class_name=self.class_name,
                year=self.today.year,
            )

    def create_user(self, email, user_type, **flags):
        self.registration += 1
        user = User.objects.create_user(
            email=email,
            password=self.password,
            name=email.split("@")[0],
            registration=self.registration,
        )
        user.user_type = user_type
        for field, value in flags.items():
            setattr(user, field, value)
        user.save()
        return user

    def create_edition(self, *, first_window_open=True, second_window_open=False):
        if first_window_open:
            initial_submission = self.today - timedelta(days=1)
            final_submission = self.today + timedelta(days=1)
        else:
            initial_submission = self.today - timedelta(days=10)
            final_submission = self.today - timedelta(days=8)

        if second_window_open:
            initial_second_submission = self.today - timedelta(days=1)
            final_second_submission = self.today + timedelta(days=1)
            initial_second_advisor = self.today - timedelta(days=1)
            final_second_advisor = self.today + timedelta(days=2)
        else:
            initial_second_submission = self.today + timedelta(days=3)
            final_second_submission = self.today + timedelta(days=4)
            initial_second_advisor = self.today + timedelta(days=3)
            final_second_advisor = self.today + timedelta(days=5)

        return Edition.objects.create(
            year=self.today.year,
            theme="Tema de Teste",
            edition_name="Edicao Teste",
            event_date=self.today,
            final_event_date=self.today + timedelta(days=10),
            initial_submission_date=initial_submission,
            final_submission_date=final_submission,
            initial_second_submission_date=initial_second_submission,
            final_second_submission_date=final_second_submission,
            initial_advisor_acceptance=self.today - timedelta(days=1),
            final_advisor_acceptance=self.today + timedelta(days=2),
            initial_second_advisor_date=initial_second_advisor,
            final_second_advisor_date=final_second_advisor,
            initial_evaluators_date=self.today - timedelta(days=1),
            final_evaluators_date=self.today + timedelta(days=20),
            members_min=2,
            members_max=4,
            collaborators_min=1,
            collaborators_max=2,
            subjects_min=1,
            subjects_max=3,
            evaluators_count=1,
            works_per_evaluator_max=3,
            works_per_collaborator_max=3,
            works_per_advisor_max=3,
            words_per_work_min=3,
            words_per_work_max=200,
            workload=10,
        )

    def create_team_via_api(self, edition):
        self.client.force_authenticate(self.student)
        response = self.client.post(
            "/api/team/",
            {
                "team_members": [self.student.id, self.student_two.id],
                "edition": edition.id,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        return Team.objects.get(id=response.data["id"])

    def work_payload(self, edition, team, title="Trabalho de Integracao"):
        return {
            "title": title,
            "abstract": "Resumo com palavras suficientes para validar o fluxo completo",
            "edition": edition.id,
            "field": [self.field.id],
            "advisor": self.advisor.id,
            "cross_cutting_theme": self.theme.id,
            "team": team.id,
            "ods": [self.ods.id],
            "collaborators": [self.collaborator.id],
            "integrated_project": False,
        }

    @patch("core.work.infra.work_django_app.views.work.send_work_email_to_advisor.delay")
    @patch("core.work.infra.work_django_app.views.work.send_work_email_to_collaborator.delay")
    def create_work_via_api(self, edition, team, collaborator_delay, advisor_delay, title="Trabalho de Integracao"):
        self.client.force_authenticate(self.student)
        response = self.client.post(
            "/api/work/",
            self.work_payload(edition, team, title=title),
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        return Work.objects.get(id=response.data["id"])

    @patch("core.work.infra.work_django_app.views.work.send_work_email_to_advisor.delay")
    @patch("core.work.infra.work_django_app.views.work.send_work_email_to_collaborator.delay")
    def test_rejects_work_when_submission_windows_are_closed(self, collaborator_delay, advisor_delay):
        edition = self.create_edition(first_window_open=False, second_window_open=False)
        team = self.create_team_via_api(edition)

        self.client.force_authenticate(self.student)
        response = self.client.post(
            "/api/work/",
            self.work_payload(edition, team, title="Fora do Prazo"),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(Work.objects.filter(title="Fora do Prazo").exists())

    def test_allows_work_with_collaborator_during_second_submission_window(self):
        edition = self.create_edition(first_window_open=False, second_window_open=True)
        team = self.create_team_via_api(edition)

        work = self.create_work_via_api(edition, team, title="Segunda Janela")

        self.assertEqual(work.status, WorkStatusType.Type.PENDING.value)
        self.assertTrue(
            WorkCollaborator.objects.filter(
                work=work,
                collaborator=self.collaborator,
                status=WorkCollaboratorStatusType.Type.PENDING.value,
            ).exists()
        )

    @patch("core.work.infra.work_django_app.views.accept_advisor_work.send_work_approve_email_to_student.delay")
    def test_rejects_advisor_acceptance_before_advisor_window(self, advisor_accept_email_delay):
        edition = self.create_edition(first_window_open=True)
        edition.initial_advisor_acceptance = self.today + timedelta(days=1)
        edition.final_advisor_acceptance = self.today + timedelta(days=3)
        edition.save()
        team = self.create_team_via_api(edition)
        work = self.create_work_via_api(edition, team, title="Aceite Futuro")

        self.client.force_authenticate(self.advisor)
        advisor_detail = self.client.get(f"/api/work/{work.id}/")
        response = self.client.get(
            f"/api/accept-advisor-work/{advisor_detail.data['verification_token']}/"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.data)

        work.refresh_from_db()
        self.assertEqual(work.advisor_status, WorkAdvisorStatusType.Type.PENDING.value)

    @patch("core.work.infra.work_django_app.views.accept_collaborator_work.send_collaborator_accept_email_to_student.delay")
    @patch("core.work.infra.work_django_app.views.approved_work.send_work_new_status_approve_email_to_student.delay")
    @patch("core.work.infra.work_django_app.views.accept_advisor_work.send_work_approve_email_to_student.delay")
    def test_complete_edition_flow_from_submission_to_report(
        self,
        advisor_accept_email_delay,
        work_approved_email_delay,
        collaborator_accept_email_delay,
    ):
        edition = self.create_edition(first_window_open=True)
        team = self.create_team_via_api(edition)
        work = self.create_work_via_api(edition, team)

        work.refresh_from_db()
        self.assertEqual(work.status, WorkStatusType.Type.PENDING.value)
        self.assertEqual(work.advisor_status, WorkAdvisorStatusType.Type.PENDING.value)

        self.client.force_authenticate(self.advisor)
        advisor_detail = self.client.get(f"/api/work/{work.id}/")
        self.assertEqual(advisor_detail.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(advisor_detail.data["verification_token"])

        accept_advisor = self.client.get(
            f"/api/accept-advisor-work/{advisor_detail.data['verification_token']}/"
        )
        self.assertEqual(accept_advisor.status_code, status.HTTP_200_OK, accept_advisor.data)

        work.refresh_from_db()
        self.assertEqual(work.advisor_status, WorkAdvisorStatusType.Type.APPROVED.value)

        advisor_detail = self.client.get(f"/api/work/{work.id}/")
        approve_work = self.client.get(
            f"/api/accept-work/{advisor_detail.data['verification_token']}/"
        )
        self.assertEqual(approve_work.status_code, status.HTTP_200_OK, approve_work.data)

        work.refresh_from_db()
        self.assertEqual(work.status, WorkStatusType.Type.APPROVED.value)

        self.client.force_authenticate(self.collaborator)
        collaborator_detail = self.client.get(f"/api/work/{work.id}/")
        collaborator_token = collaborator_detail.data["work_collaborator"][0]["verification_token"]
        self.assertIsNotNone(collaborator_token)

        accept_collaborator = self.client.get(
            f"/api/accept-collaborator-work/{collaborator_token}/"
        )
        self.assertEqual(accept_collaborator.status_code, status.HTTP_200_OK, accept_collaborator.data)

        collaborator_link = WorkCollaborator.objects.get(work=work, collaborator=self.collaborator)
        self.assertEqual(collaborator_link.status, WorkCollaboratorStatusType.Type.APPROVED.value)

        work.evaluator.add(self.evaluator)

        self.client.force_authenticate(self.evaluator_user)
        assessment_response = self.client.post(
            "/api/assessment/",
            {
                "evaluator": self.evaluator.id,
                "work": str(work.id),
                "grade": "8.50",
                "date_time": timezone.now().isoformat(),
                "committee_feedback": "Avaliacao registrada.",
            },
            format="json",
        )
        self.assertEqual(assessment_response.status_code, status.HTTP_201_CREATED, assessment_response.data)
        self.assertTrue(
            Assessment.objects.filter(work=work, evaluator=self.evaluator, grade=Decimal("8.50")).exists()
        )

        self.client.force_authenticate(self.advisor)
        student_assessment_response = self.client.post(
            "/api/student-assessments/",
            {
                "student": self.student.id,
                "work": str(work.id),
                "grade": "9.00",
                "date_time": timezone.now().isoformat(),
            },
            format="json",
        )
        self.assertEqual(
            student_assessment_response.status_code,
            status.HTTP_201_CREATED,
            student_assessment_response.data,
        )
        self.assertTrue(
            StudentAssessments.objects.filter(work=work, student=self.student, grade=Decimal("9.00")).exists()
        )

        report_response = self.client.get(f"/api/generate-assessment-report/{edition.year}/")
        self.assertEqual(report_response.status_code, status.HTTP_200_OK)
        self.assertIn("application/pdf", report_response["Content-Type"])
