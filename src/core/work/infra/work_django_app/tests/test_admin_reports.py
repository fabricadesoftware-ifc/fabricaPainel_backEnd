from datetime import timedelta

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


class AdminAdvisorReportApiTest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.today = timezone.localdate()
        self.password = "test-password-123"
        self.registration = 2026020000

        self.admin = self.create_user("admin.report@test.local", UserType.Type.ADMIN.value)
        self.manager = self.create_user(
            "manager.report@test.local",
            UserType.Type.TEACHER.value,
            is_management=True,
        )
        self.teacher = self.create_user("teacher.report@test.local", UserType.Type.TEACHER.value)
        self.student = self.create_user("student.report@test.local", UserType.Type.STUDENT.value)
        self.student_two = self.create_user("student2.report@test.local", UserType.Type.STUDENT.value)
        self.other_student = self.create_user("other.report@test.local", UserType.Type.STUDENT.value)
        self.advisor = self.create_user(
            "advisor.report@test.local",
            UserType.Type.TEACHER.value,
            is_advisor=True,
        )
        self.advisor_two = self.create_user(
            "advisor2.report@test.local",
            UserType.Type.TEACHER.value,
            is_advisor=True,
        )
        self.collaborator = self.create_user(
            "collaborator.report@test.local",
            UserType.Type.TEACHER.value,
            is_collaborator=True,
        )

        self.field = Field.objects.create(name="Report Field")
        self.theme = CrossCuttingTheme.objects.create(name="Report Theme")
        self.ods = Ods.objects.create(name="Report ODS")
        self.edition = self.create_edition(final_second_advisor_offset=-1)
        self.pending_edition = self.create_edition(final_second_advisor_offset=1, year=self.today.year + 1)

        self.class_name = Class.objects.create(name="1INFO1")
        self.other_class_name = Class.objects.create(name="2INFO1")
        UserClass.objects.create(user=self.student, class_name=self.class_name, year=self.edition.year)
        UserClass.objects.create(user=self.student_two, class_name=self.class_name, year=self.edition.year)
        UserClass.objects.create(user=self.other_student, class_name=self.other_class_name, year=self.edition.year)

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

    def create_edition(self, *, final_second_advisor_offset, year=None):
        return Edition.objects.create(
            year=year or self.today.year,
            theme="Report Theme",
            edition_name=f"Report Edition {year or self.today.year}",
            event_date=self.today + timedelta(days=20),
            final_event_date=self.today + timedelta(days=21),
            initial_submission_date=self.today - timedelta(days=30),
            final_submission_date=self.today - timedelta(days=25),
            initial_second_submission_date=self.today - timedelta(days=15),
            final_second_submission_date=self.today - timedelta(days=10),
            initial_advisor_acceptance=self.today - timedelta(days=30),
            final_advisor_acceptance=self.today - timedelta(days=25),
            initial_second_advisor_date=self.today - timedelta(days=15),
            final_second_advisor_date=self.today + timedelta(days=final_second_advisor_offset),
            initial_evaluators_date=self.today + timedelta(days=20),
            final_evaluators_date=self.today + timedelta(days=25),
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

    def create_team(self, members, edition=None):
        team = Team.objects.create(edition=edition or self.edition)
        team.team_members.set(members)
        return team

    def create_work(
        self,
        title,
        members,
        *,
        advisor=None,
        collaborator_status=None,
        work_status=None,
        advisor_status=None,
    ):
        work = Work.objects.create(
            title=title,
            abstract="Resumo com conteudo suficiente para relatorio administrativo.",
            edition=self.edition,
            cross_cutting_theme=self.theme,
            team=self.create_team(members),
            advisor=advisor or self.advisor,
            advisor_status=advisor_status or WorkAdvisorStatusType.Type.APPROVED.value,
            status=work_status or WorkStatusType.Type.PENDING.value,
            integrated_project=False,
        )
        work.field.set([self.field])
        work.ods.set([self.ods])

        if collaborator_status is not None:
            WorkCollaborator.objects.create(
                work=work,
                collaborator=self.collaborator,
                status=collaborator_status,
            )

        return work

    def test_admin_and_management_can_generate_advisor_report_pdf(self):
        self.create_work(
            "Trabalho com PDF",
            [self.student, self.other_student],
            collaborator_status=WorkCollaboratorStatusType.Type.APPROVED.value,
        )

        for user in (self.admin, self.manager):
            self.client.force_authenticate(user)
            response = self.client.get(
                "/api/work/admin-advisor-report/",
                {"edition": self.edition.id},
            )

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIn("application/pdf", response["Content-Type"])

    def test_common_users_cannot_access_advisor_report(self):
        for user in (self.teacher, self.student):
            self.client.force_authenticate(user)
            response = self.client.get(
                "/api/work/admin-advisor-report-data/",
                {"edition": self.edition.id},
            )

            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.data)

    def test_report_data_groups_by_advisor_and_keeps_mixed_classes_in_the_same_work(self):
        mixed_class_work = self.create_work(
            "Trabalho com turmas mistas",
            [self.student, self.other_student],
            collaborator_status=WorkCollaboratorStatusType.Type.APPROVED.value,
        )
        without_collaborator = self.create_work(
            "Trabalho sem colaborador",
            [self.student, self.student_two],
        )
        advisor_two_work = self.create_work(
            "Trabalho de outro orientador",
            [self.student_two],
            advisor=self.advisor_two,
            collaborator_status=WorkCollaboratorStatusType.Type.APPROVED.value,
        )
        self.create_work(
            "Trabalho com ajuste pendente",
            [self.student, self.student_two],
            work_status=WorkStatusType.Type.NEEDS_CHANGES.value,
        )

        self.client.force_authenticate(self.admin)
        response = self.client.get(
            "/api/work/admin-advisor-report-data/",
            {"edition": self.edition.id},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertTrue(response.data["available"])
        self.assertEqual(response.data["total_works"], 3)
        self.assertEqual(len(response.data["groups"]), 2)

        groups_by_advisor = {
            group["advisor"]["id"]: group
            for group in response.data["groups"]
        }
        first_group_rows = {
            row["id"]: row
            for row in groups_by_advisor[self.advisor.id]["rows"]
        }

        self.assertIn(str(mixed_class_work.id), first_group_rows)
        self.assertIn(str(without_collaborator.id), first_group_rows)
        mixed_row = first_group_rows[str(mixed_class_work.id)]
        members_by_id = {
            member["id"]: member
            for member in mixed_row["team_members"]
        }
        self.assertIn("1INFO1", mixed_row["classes_label"])
        self.assertIn("2INFO1", mixed_row["classes_label"])
        self.assertIn("1INFO1", mixed_row["team_members_label"])
        self.assertIn("2INFO1", mixed_row["team_members_label"])
        self.assertEqual(members_by_id[self.student.id]["classes_label"], "1INFO1")
        self.assertEqual(members_by_id[self.other_student.id]["classes_label"], "2INFO1")
        self.assertEqual(mixed_row["collaborators"][0]["id"], self.collaborator.id)
        self.assertEqual(first_group_rows[str(without_collaborator.id)]["collaborators"], [])
        self.assertEqual(first_group_rows[str(without_collaborator.id)]["collaborators_label"], "Sem colaborador")
        self.assertEqual(groups_by_advisor[self.advisor_two.id]["rows"][0]["id"], str(advisor_two_work.id))

    def test_report_is_not_available_until_after_second_advisor_acceptance_period(self):
        self.client.force_authenticate(self.admin)
        data_response = self.client.get(
            "/api/work/admin-advisor-report-data/",
            {"edition": self.pending_edition.id},
        )
        pdf_response = self.client.get(
            "/api/work/admin-advisor-report/",
            {"edition": self.pending_edition.id},
        )

        self.assertEqual(data_response.status_code, status.HTTP_200_OK, data_response.data)
        self.assertFalse(data_response.data["available"])
        self.assertEqual(data_response.data["groups"], [])
        self.assertEqual(pdf_response.status_code, status.HTTP_400_BAD_REQUEST, pdf_response.data)
