from datetime import timedelta
from decimal import Decimal

from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from core.assessment.infra.assessment_django_app.models import Assessment, StudentAssessments
from core.cross_cutting_themes.infra.cross_cutting_themes_django_app.models import CrossCuttingTheme
from core.edition.infra.edition_django_app.models import Edition
from core.field.infra.field_django_app.models import Field
from core.user.domain.value_objects import UserType
from core.user.infra.user_django_app.models import Evaluator, User
from core.work.domain.value_objects import WorkAdvisorStatusType, WorkStatusType
from core.work.infra.work_django_app.models import Ods, Team, Work


class AdminGradingOverviewApiTest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.today = timezone.localdate()
        self.registration = 2026020000
        self.password = "test-password-123"

        self.admin = self.create_user("admin.grading@test.local", UserType.Type.ADMIN.value)
        self.manager = self.create_user(
            "manager.grading@test.local", UserType.Type.TEACHER.value, is_management=True
        )
        self.teacher = self.create_user("teacher.grading@test.local", UserType.Type.TEACHER.value)
        self.student = self.create_user("student.grading@test.local", UserType.Type.STUDENT.value)
        self.advisor = self.create_user(
            "advisor.grading@test.local", UserType.Type.TEACHER.value, is_advisor=True
        )
        self.evaluator_user = self.create_user("evaluator.grading@test.local", UserType.Type.TEACHER.value)
        self.evaluator = Evaluator.objects.create(user=self.evaluator_user)

        self.field = Field.objects.create(name="Grading Field")
        self.theme = CrossCuttingTheme.objects.create(name="Grading Theme")
        self.ods = Ods.objects.create(name="Grading ODS")
        self.edition = self.create_edition()

    def create_user(self, email, user_type, **flags):
        self.registration += 1
        user = User.objects.create_user(
            email=email, password=self.password, name=email.split("@")[0], registration=self.registration
        )
        user.user_type = user_type
        for field, value in flags.items():
            setattr(user, field, value)
        user.save()
        return user

    def create_edition(self):
        return Edition.objects.create(
            year=self.today.year,
            theme="Grading Theme",
            edition_name="Grading Edition",
            event_date=self.today - timedelta(days=5),
            final_event_date=self.today + timedelta(days=5),
            initial_submission_date=self.today - timedelta(days=20),
            final_submission_date=self.today - timedelta(days=18),
            initial_second_submission_date=self.today - timedelta(days=17),
            final_second_submission_date=self.today - timedelta(days=16),
            initial_advisor_acceptance=self.today - timedelta(days=15),
            final_advisor_acceptance=self.today - timedelta(days=13),
            initial_second_advisor_date=self.today - timedelta(days=12),
            final_second_advisor_date=self.today - timedelta(days=10),
            initial_evaluators_date=self.today - timedelta(days=1),
            final_evaluators_date=self.today + timedelta(days=5),
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

    def create_team(self, student=None):
        team = Team.objects.create(edition=self.edition)
        team.team_members.set([student or self.student])
        return team

    def create_work(self, title, *, student=None, status_value=WorkStatusType.Type.APPROVED.value):
        work = Work.objects.create(
            title=title,
            abstract="Resumo com conteudo suficiente para o teste.",
            edition=self.edition,
            cross_cutting_theme=self.theme,
            team=self.create_team(student),
            advisor=self.advisor,
            advisor_status=WorkAdvisorStatusType.Type.APPROVED.value,
            status=status_value,
            verification_token=f"token-{title}",
            integrated_project=False,
        )
        work.field.set([self.field])
        work.ods.set([self.ods])
        work.evaluator.set([self.evaluator])
        return work

    def grade_by_advisor(self, work, student):
        StudentAssessments.objects.create(
            work=work, student=student, grade=Decimal("8.00"), date_time=timezone.now()
        )

    def grade_by_evaluator(self, work):
        Assessment.objects.create(
            work=work, evaluator=self.evaluator, grade=Decimal("9.00"), date_time=timezone.now()
        )

    def get_column(self, response, key):
        return next(column for column in response.data["columns"] if column["key"] == key)

    def test_admin_and_management_users_can_access(self):
        for user in (self.admin, self.manager):
            self.client.force_authenticate(user)
            response = self.client.get(f"/api/work/admin-grading-overview/?edition={self.edition.id}")
            self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)

    def test_common_teacher_and_student_cannot_access(self):
        for user in (self.teacher, self.student):
            self.client.force_authenticate(user)
            response = self.client.get(f"/api/work/admin-grading-overview/?edition={self.edition.id}")
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.data)

    def test_splits_works_by_who_already_graded(self):
        only_advisor = self.create_work("So orientador avaliou")
        self.grade_by_advisor(only_advisor, self.student)

        only_evaluator = self.create_work("So avaliador avaliou")
        self.grade_by_evaluator(only_evaluator)

        complete = self.create_work("Completo")
        self.grade_by_advisor(complete, self.student)
        self.grade_by_evaluator(complete)

        not_graded_yet = self.create_work("Sem nenhuma nota")

        self.client.force_authenticate(self.admin)
        response = self.client.get(f"/api/work/admin-grading-overview/?edition={self.edition.id}")

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)

        advisor_only_ids = {item["id"] for item in self.get_column(response, "advisor_only")["items"]}
        evaluator_only_ids = {item["id"] for item in self.get_column(response, "evaluator_only")["items"]}
        complete_ids = {item["id"] for item in self.get_column(response, "complete")["items"]}

        self.assertEqual(advisor_only_ids, {str(only_advisor.id)})
        self.assertEqual(evaluator_only_ids, {str(only_evaluator.id)})
        self.assertEqual(complete_ids, {str(complete.id)})
        self.assertNotIn(str(not_graded_yet.id), advisor_only_ids | evaluator_only_ids | complete_ids)

    def test_excludes_works_that_are_not_approved(self):
        pending_work = self.create_work("Ainda pendente", status_value=WorkStatusType.Type.PENDING.value)
        self.grade_by_advisor(pending_work, self.student)
        self.grade_by_evaluator(pending_work)

        self.client.force_authenticate(self.admin)
        response = self.client.get(f"/api/work/admin-grading-overview/?edition={self.edition.id}")

        all_ids = {
            item["id"]
            for column in response.data["columns"]
            for item in column["items"]
        }
        self.assertNotIn(str(pending_work.id), all_ids)

    def test_shows_the_grades_given(self):
        work = self.create_work("Com notas visiveis")
        self.grade_by_advisor(work, self.student)
        self.grade_by_evaluator(work)

        self.client.force_authenticate(self.admin)
        response = self.client.get(f"/api/work/admin-grading-overview/?edition={self.edition.id}")

        item = self.get_column(response, "complete")["items"][0]
        self.assertEqual(item["student_grades"][0]["grade"], "8.00")
        self.assertEqual(item["evaluator_grades"][0]["grade"], "9.00")

    def test_query_count_does_not_grow_with_the_number_of_works(self):
        self.client.force_authenticate(self.admin)

        def create_batch(count, offset):
            for i in range(count):
                student = self.create_user(f"batch.student.{offset + i}@test.local", UserType.Type.STUDENT.value)
                work = self.create_work(f"Trabalho {offset + i}", student=student)
                self.grade_by_advisor(work, student)

        create_batch(2, offset=0)
        with CaptureQueriesContext(connection) as small_batch:
            response = self.client.get(f"/api/work/admin-grading-overview/?edition={self.edition.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)

        create_batch(10, offset=2)
        with CaptureQueriesContext(connection) as large_batch:
            response = self.client.get(f"/api/work/admin-grading-overview/?edition={self.edition.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)

        self.assertLess(
            len(large_batch.captured_queries) - len(small_batch.captured_queries),
            5,
            "numero de queries cresceu junto com a quantidade de trabalhos (N+1)",
        )

    # ---- popup de detalhe (admin-detail) ----

    def set_weights(self, work_weight, student_weight):
        def block(key, target, label, weight, criterion_key):
            return {
                "key": key,
                "target": target,
                "label": label,
                "weight": weight,
                "criteria": [{"key": criterion_key, "label": "Nota geral", "weight": 100, "description": ""}],
            }

        self.edition.evaluation_criteria = [
            block("work", "work", "Nota do avaliador", work_weight, "work_general"),
            block("student", "student", "Nota do orientador", student_weight, "student_general"),
        ]
        self.edition.save()

    def detail_url(self, work):
        return f"/api/work/{work.id}/admin-detail/"

    def test_admin_detail_is_restricted_to_admin_and_management(self):
        work = self.create_work("Detalhe permissao")

        for user in (self.admin, self.manager):
            self.client.force_authenticate(user)
            self.assertEqual(self.client.get(self.detail_url(work)).status_code, status.HTTP_200_OK)

        for user in (self.teacher, self.student, self.advisor, self.evaluator_user):
            self.client.force_authenticate(user)
            self.assertEqual(
                self.client.get(self.detail_url(work)).status_code, status.HTTP_403_FORBIDDEN
            )

    def test_admin_detail_returns_404_for_unknown_or_invalid_id(self):
        self.client.force_authenticate(self.admin)

        self.assertEqual(
            self.client.get("/api/work/00000000-0000-0000-0000-000000000000/admin-detail/").status_code,
            status.HTTP_404_NOT_FOUND,
        )
        self.assertEqual(
            self.client.get("/api/work/nao-e-uuid/admin-detail/").status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_admin_detail_shows_everything_with_weighted_final_grade(self):
        self.set_weights(40, 60)
        work = self.create_work("Detalhe completo")
        self.grade_by_advisor(work, self.student)  # nota do orientador: 8.00
        self.grade_by_evaluator(work)  # nota da banca: 9.00

        self.client.force_authenticate(self.admin)
        data = self.client.get(self.detail_url(work)).data

        self.assertEqual(data["title"], "Detalhe completo")
        self.assertEqual(data["advisor"]["email"], self.advisor.email)
        self.assertEqual(data["weights"], {"work": 40.0, "student": 60.0})
        self.assertEqual(data["evaluators"][0]["assessment"]["grade"], "9.00")
        self.assertEqual(data["work_grade_average"], "9.00")
        # id da nota e criterios da edicao: o admin lanca/edita nota pelo popup.
        self.assertTrue(data["evaluators"][0]["assessment"]["id"])
        self.assertEqual(data["criteria"]["work"][0]["key"], "work_general")
        self.assertEqual(data["criteria"]["student"][0]["key"], "student_general")

        member = data["team_members"][0]
        self.assertEqual(member["email"], self.student.email)
        self.assertEqual(member["advisor_assessment"]["grade"], "8.00")
        # (8.00 * 60 + 9.00 * 40) / 100 = 8.40, mesma formula do relatorio de notas
        self.assertEqual(member["final_grade"], "8.40")
        self.assertEqual(member["situation"], "Aprovado")

    def test_admin_detail_marks_failing_final_grade(self):
        self.set_weights(50, 50)
        work = self.create_work("Detalhe reprovado")
        StudentAssessments.objects.create(
            work=work, student=self.student, grade=Decimal("4.00"), date_time=timezone.now()
        )
        Assessment.objects.create(
            work=work, evaluator=self.evaluator, grade=Decimal("6.00"), date_time=timezone.now()
        )

        self.client.force_authenticate(self.admin)
        member = self.client.get(self.detail_url(work)).data["team_members"][0]

        self.assertEqual(member["final_grade"], "5.00")
        self.assertEqual(member["situation"], "Reprovado")

    def test_admin_detail_has_no_final_grade_while_something_is_pending(self):
        work = self.create_work("Detalhe pendente")
        self.grade_by_advisor(work, self.student)  # banca ainda nao avaliou

        self.client.force_authenticate(self.admin)
        data = self.client.get(self.detail_url(work)).data

        self.assertIsNone(data["work_grade_average"])
        self.assertIsNone(data["evaluators"][0]["assessment"])
        self.assertIsNone(data["team_members"][0]["final_grade"])
        self.assertIsNone(data["team_members"][0]["situation"])
        self.assertEqual(data["team_members"][0]["advisor_assessment"]["grade"], "8.00")

