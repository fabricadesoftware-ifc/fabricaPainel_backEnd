from datetime import timedelta
from unittest.mock import patch

from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from core.cross_cutting_themes.infra.cross_cutting_themes_django_app.models import CrossCuttingTheme
from core.edition.infra.edition_django_app.models import Edition
from core.field.infra.field_django_app.models import Field
from core.user.domain.value_objects import UserType
from core.user.infra.user_django_app.models import Class, User, UserClass
from core.work.domain.value_objects import (
    WorkAdvisorStatusType,
    WorkCollaboratorStatusType,
    WorkStatusType,
)
from core.work.infra.work_django_app.models import Ods, Team, Work, WorkCollaborator


class AdminKanbanApiTest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.today = timezone.localdate()
        self.registration = 2026010000
        self.password = "test-password-123"

        self.admin = self.create_user("admin.kanban@test.local", UserType.Type.ADMIN.value)
        self.manager = self.create_user(
            "manager.kanban@test.local",
            UserType.Type.TEACHER.value,
            is_management=True,
        )
        self.teacher = self.create_user("teacher.kanban@test.local", UserType.Type.TEACHER.value)
        self.student = self.create_user("student.kanban@test.local", UserType.Type.STUDENT.value)
        self.student_two = self.create_user("student2.kanban@test.local", UserType.Type.STUDENT.value)
        self.advisor = self.create_user(
            "advisor.kanban@test.local",
            UserType.Type.TEACHER.value,
            is_advisor=True,
        )
        self.collaborator = self.create_user(
            "collaborator.kanban@test.local",
            UserType.Type.TEACHER.value,
            is_collaborator=True,
        )

        self.field = Field.objects.create(name="Kanban Field")
        self.theme = CrossCuttingTheme.objects.create(name="Kanban Theme")
        self.ods = Ods.objects.create(name="Kanban ODS")
        self.edition = self.create_edition()
        self.class_name = Class.objects.create(name="1INFO1")
        UserClass.objects.create(user=self.student, class_name=self.class_name, year=self.edition.year)
        UserClass.objects.create(user=self.student_two, class_name=self.class_name, year=self.edition.year)

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

    def create_edition(self):
        return Edition.objects.create(
            year=self.today.year,
            theme="Kanban Theme",
            edition_name="Kanban Edition",
            event_date=self.today + timedelta(days=8),
            final_event_date=self.today + timedelta(days=9),
            initial_submission_date=self.today - timedelta(days=2),
            final_submission_date=self.today + timedelta(days=2),
            initial_second_submission_date=self.today + timedelta(days=3),
            final_second_submission_date=self.today + timedelta(days=4),
            initial_advisor_acceptance=self.today - timedelta(days=2),
            final_advisor_acceptance=self.today + timedelta(days=2),
            initial_second_advisor_date=self.today + timedelta(days=3),
            final_second_advisor_date=self.today + timedelta(days=5),
            initial_evaluators_date=self.today + timedelta(days=8),
            final_evaluators_date=self.today + timedelta(days=10),
            members_min=1,
            members_max=4,
            collaborators_min=0,
            collaborators_max=2,
            subjects_min=1,
            subjects_max=3,
            evaluators_count=1,
            works_per_evaluator_max=5,
            works_per_collaborator_max=5,
            works_per_advisor_max=5,
            words_per_work_min=3,
            words_per_work_max=200,
            workload=10,
        )

    def create_team(self):
        team = Team.objects.create(edition=self.edition)
        team.team_members.set([self.student, self.student_two])
        return team

    def create_work(self, title, *, work_status, advisor_status, collaborator_status=None):
        work = Work.objects.create(
            title=title,
            abstract="Resumo com conteudo suficiente para o kanban administrativo.",
            edition=self.edition,
            cross_cutting_theme=self.theme,
            team=self.create_team(),
            advisor=self.advisor,
            advisor_status=advisor_status,
            status=work_status,
            verification_token=f"token-{title}",
            integrated_project=False,
        )
        work.field.set([self.field])
        work.ods.set([self.ods])

        if collaborator_status is not None:
            WorkCollaborator.objects.create(
                work=work,
                collaborator=self.collaborator,
                status=collaborator_status,
                verification_token=f"collab-token-{title}",
            )

        return work

    def get_column(self, response, key):
        return next(column for column in response.data["columns"] if column["key"] == key)

    def test_admin_and_management_users_can_access_admin_kanban(self):
        for user in (self.admin, self.manager):
            self.client.force_authenticate(user)
            response = self.client.get(f"/api/work/admin-kanban/?edition={self.edition.id}")

            self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)

    def test_common_teacher_and_student_cannot_access_admin_kanban(self):
        for user in (self.teacher, self.student):
            self.client.force_authenticate(user)
            response = self.client.get(f"/api/work/admin-kanban/?edition={self.edition.id}")

            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.data)

    def test_groups_works_by_operational_situation_and_keeps_collaborators_optional(self):
        self.create_work(
            "Aguardando orientador",
            work_status=WorkStatusType.Type.PENDING.value,
            advisor_status=WorkAdvisorStatusType.Type.PENDING.value,
        )
        self.create_work(
            "Orientador recusou",
            work_status=WorkStatusType.Type.PENDING.value,
            advisor_status=WorkAdvisorStatusType.Type.REJECTED.value,
        )
        self.create_work(
            "Precisa de ajustes",
            work_status=WorkStatusType.Type.NEEDS_CHANGES.value,
            advisor_status=WorkAdvisorStatusType.Type.APPROVED.value,
            collaborator_status=WorkCollaboratorStatusType.Type.PENDING.value,
        )
        ready_work = self.create_work(
            "Orientador aceitou sem colaborador",
            work_status=WorkStatusType.Type.PENDING.value,
            advisor_status=WorkAdvisorStatusType.Type.APPROVED.value,
        )
        self.create_work(
            "Trabalho aprovado",
            work_status=WorkStatusType.Type.APPROVED.value,
            advisor_status=WorkAdvisorStatusType.Type.APPROVED.value,
            collaborator_status=WorkCollaboratorStatusType.Type.APPROVED.value,
        )
        self.create_work(
            "Trabalho rejeitado",
            work_status=WorkStatusType.Type.REJECTED.value,
            advisor_status=WorkAdvisorStatusType.Type.APPROVED.value,
        )
        self.create_work(
            "Expirado",
            work_status=WorkStatusType.Type.EXPIRED.value,
            advisor_status=WorkAdvisorStatusType.Type.EXPIRED.value,
        )

        self.client.force_authenticate(self.admin)
        response = self.client.get(f"/api/work/admin-kanban/?edition={self.edition.id}")

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(self.get_column(response, "waiting_advisor")["count"], 1)
        self.assertEqual(self.get_column(response, "advisor_rejected")["count"], 1)
        self.assertEqual(self.get_column(response, "needs_changes")["count"], 1)
        self.assertEqual(self.get_column(response, "ready")["count"], 1)
        self.assertEqual(self.get_column(response, "approved")["count"], 1)
        self.assertEqual(self.get_column(response, "rejected")["count"], 1)
        self.assertEqual(self.get_column(response, "expired")["count"], 1)

        ready_item = self.get_column(response, "ready")["items"][0]
        self.assertEqual(ready_item["id"], str(ready_work.id))
        self.assertFalse(ready_item["has_collaborators"])
        self.assertEqual(ready_item["collaborators"], [])

    def test_searches_by_title_student_advisor_and_collaborator(self):
        work = self.create_work(
            "Busca por Titulo Especial",
            work_status=WorkStatusType.Type.PENDING.value,
            advisor_status=WorkAdvisorStatusType.Type.APPROVED.value,
            collaborator_status=WorkCollaboratorStatusType.Type.PENDING.value,
        )

        self.client.force_authenticate(self.admin)
        for query in ("Titulo Especial", self.student.name, self.advisor.email, self.collaborator.name, "1info1"):
            response = self.client.get(
                "/api/work/admin-kanban/",
                {"edition": self.edition.id, "search": query},
            )

            self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
            self.assertEqual(self.get_column(response, "ready")["items"][0]["id"], str(work.id))

    @patch("core.work.infra.work_django_app.views.accept_collaborator_work.send_collaborator_accept_email_to_student.delay")
    @patch("core.work.infra.work_django_app.views.accept_advisor_work.send_work_approve_email_to_student.delay")
    def test_status_actions_create_historical_records(self, advisor_email_delay, collaborator_email_delay):
        work = self.create_work(
            "Historico de aceite",
            work_status=WorkStatusType.Type.PENDING.value,
            advisor_status=WorkAdvisorStatusType.Type.PENDING.value,
            collaborator_status=WorkCollaboratorStatusType.Type.PENDING.value,
        )
        collaborator_link = WorkCollaborator.objects.get(work=work)

        self.client.force_authenticate(self.advisor)
        response = self.client.get(f"/api/accept-advisor-work/{work.verification_token}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)

        self.client.force_authenticate(self.collaborator)
        response = self.client.get(f"/api/accept-collaborator-work/{collaborator_link.verification_token}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)

        work.refresh_from_db()
        collaborator_link.refresh_from_db()

        self.assertEqual(work.history.first().history_change_reason, "Orientador aceitou")
        self.assertEqual(collaborator_link.history.first().history_change_reason, "Colaborador aceitou")

        self.client.force_authenticate(self.admin)
        response = self.client.get(
            "/api/work/admin-kanban/",
            {"edition": self.edition.id, "search": "Historico"},
        )
        timeline_events = [
            event["event"]
            for event in self.get_column(response, "ready")["items"][0]["timeline"]
        ]

        self.assertIn("Orientador aceitou", timeline_events)
        self.assertIn("Colaborador aceitou", timeline_events)

    def test_query_count_does_not_grow_with_the_number_of_works(self):
        # `instance.history` do simple_history não é uma relação de verdade, então
        # prefetch_related não serve nela — sem buscar o histórico em lote, cada
        # trabalho (e cada colaborador) soma consultas, e a tela trava com muitos
        # trabalhos (visto na prática: ~700 queries para ~100 trabalhos).
        self.client.force_authenticate(self.admin)

        def create_batch(count, offset):
            for i in range(count):
                self.create_work(
                    f"Trabalho {offset + i}",
                    work_status=WorkStatusType.Type.PENDING.value,
                    advisor_status=WorkAdvisorStatusType.Type.APPROVED.value,
                    collaborator_status=WorkCollaboratorStatusType.Type.PENDING.value,
                )

        create_batch(2, offset=0)
        with CaptureQueriesContext(connection) as small_batch:
            response = self.client.get(f"/api/work/admin-kanban/?edition={self.edition.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)

        create_batch(10, offset=2)
        with CaptureQueriesContext(connection) as large_batch:
            response = self.client.get(f"/api/work/admin-kanban/?edition={self.edition.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)

        # 12 trabalhos a mais devem somar poucas queries extras (paginação/contagem
        # de edição etc.), não uma por trabalho/colaborador/evento de histórico.
        self.assertLess(
            len(large_batch.captured_queries) - len(small_batch.captured_queries),
            5,
            "numero de queries cresceu junto com a quantidade de trabalhos (N+1)",
        )
