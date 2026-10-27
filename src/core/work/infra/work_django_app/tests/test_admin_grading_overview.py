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
        not_graded_ids = {item["id"] for item in self.get_column(response, "not_graded")["items"]}

        self.assertEqual(not_graded_ids, {str(not_graded_yet.id)})
        self.assertEqual(advisor_only_ids, {str(only_advisor.id)})
        self.assertEqual(evaluator_only_ids, {str(only_evaluator.id)})
        self.assertEqual(complete_ids, {str(complete.id)})
        self.assertNotIn(str(not_graded_yet.id), advisor_only_ids | evaluator_only_ids | complete_ids)
        # "Não avaliado" é a primeira coluna, antes de "Só o orientador avaliou".
        self.assertEqual(
            [column["key"] for column in response.data["columns"]][:2],
            ["not_graded", "advisor_only"],
        )

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



class ModuleWorkGradingTest(AdminGradingOverviewApiTest):
    """Modulos (Territorios/Comunicacao) tem nota fisica: a nota do aluno e a final."""

    overview_url = "/api/work/admin-grading-overview/"

    def detail_url(self, work):
        return f"/api/work/{work.id}/admin-detail/"

    def create_module_work(self, title, kind="territorios"):
        work = self.create_work(title)
        work.work_kind = kind
        work.evaluator.clear()  # modulo nao tem banca
        work.save()
        return work

    def test_new_works_are_regular_by_default(self):
        work = self.create_work("Comum")
        self.assertEqual(work.work_kind, "regular")
        self.assertFalse(work.is_module)

    def test_module_final_grade_is_the_student_grade_without_averaging(self):
        work = self.create_module_work("Territorios")
        StudentAssessments.objects.create(
            work=work, student=self.student, grade=Decimal("9.50"), date_time=timezone.now()
        )

        self.client.force_authenticate(self.admin)
        data = self.client.get(self.detail_url(work)).data

        self.assertEqual(data["work_kind"], "territorios")
        self.assertTrue(data["is_module"])
        self.assertEqual(data["weights"], {"work": 0.0, "student": 100.0})
        member = data["team_members"][0]
        self.assertEqual(member["final_grade"], "9.50")
        self.assertEqual(member["situation"], "Aprovado")

    def test_module_failing_physical_grade_is_marked_failed(self):
        work = self.create_module_work("Comunicacao", kind="comunicacao")
        StudentAssessments.objects.create(
            work=work, student=self.student, grade=Decimal("5.00"), date_time=timezone.now()
        )

        self.client.force_authenticate(self.admin)
        member = self.client.get(self.detail_url(work)).data["team_members"][0]

        self.assertEqual(member["final_grade"], "5.00")
        self.assertEqual(member["situation"], "Reprovado")

    def test_module_goes_to_complete_when_every_student_has_a_grade(self):
        graded = self.create_module_work("Modulo com nota")
        self.grade_by_advisor(graded, self.student)
        other_student = self.create_user("other.module@test.local", UserType.Type.STUDENT.value)
        pending = self.create_module_work("Modulo sem nota")
        pending.team.team_members.set([other_student])

        self.client.force_authenticate(self.admin)
        response = self.client.get(self.overview_url)

        complete = [item["title"] for item in self.get_column(response, "complete")["items"]]
        not_graded = [item["title"] for item in self.get_column(response, "not_graded")["items"]]
        self.assertEqual(complete, ["Modulo com nota"])
        self.assertEqual(not_graded, ["Modulo sem nota"])
        item = self.get_column(response, "complete")["items"][0]
        self.assertEqual(item["work_kind"], "territorios")

    def test_regular_work_still_needs_the_board_to_be_complete(self):
        work = self.create_work("Regular")
        self.grade_by_advisor(work, self.student)

        self.client.force_authenticate(self.admin)
        response = self.client.get(self.overview_url)

        self.assertEqual(self.get_column(response, "complete")["count"], 0)
        self.assertEqual(self.get_column(response, "advisor_only")["count"], 1)

    def test_grades_report_uses_physical_grade_for_module_students(self):
        from core.assessment.domain.assessment_datas import prepare_grades
        from core.user.infra.user_django_app.models import Class, UserClass

        module_student = self.create_user("module.report@test.local", UserType.Type.STUDENT.value)
        regular = self.create_work("Regular no relatorio")
        self.grade_by_advisor(regular, self.student)  # 8.00
        self.grade_by_evaluator(regular)  # 9.00
        module = self.create_module_work("Modulo no relatorio")
        module.team.team_members.set([module_student])
        StudentAssessments.objects.create(
            work=module, student=module_student, grade=Decimal("9.50"), date_time=timezone.now()
        )

        turma = Class.objects.create(name="3info1")
        for user in (self.student, module_student):
            UserClass.objects.create(class_name=turma, user=user, year=self.edition.year)

        report = prepare_grades(self.edition.year, class_name="3info1")
        scores = {e["student"]: e["average_score"] for e in report[0]["students"]}

        self.assertEqual(scores[module_student.name], Decimal("9.50"))
        self.assertEqual(scores[self.student.name], Decimal("8.50"))  # 50/50 de 8.00 e 9.00


class GradesReportAccessTest(AdminGradingOverviewApiTest):
    """Relatório de notas: só admin/gestão e só depois do fim do evento."""

    def report_url(self):
        return f"/api/generate-assessment-report/{self.edition.year}/"

    def status_url(self):
        return f"/api/assessment-report-status/{self.edition.year}/"

    def finish_event(self):
        self.edition.final_event_date = self.today - timedelta(days=1)
        self.edition.save()

    def test_status_says_when_report_releases(self):
        self.client.force_authenticate(self.admin)
        data = self.client.get(self.status_url()).data

        self.assertFalse(data["available"])
        self.assertEqual(
            data["available_after"], (self.edition.final_event_date + timedelta(days=1)).isoformat()
        )
        self.assertIn("disponível a partir de", data["message"])

    def test_status_available_after_event_ends(self):
        self.finish_event()
        self.client.force_authenticate(self.manager)

        self.assertTrue(self.client.get(self.status_url()).data["available"])

    def test_download_blocked_before_release_even_for_admin(self):
        self.client.force_authenticate(self.admin)
        response = self.client.get(self.report_url())

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data["available_after"],
            (self.edition.final_event_date + timedelta(days=1)).isoformat(),
        )

    def test_regular_teacher_and_student_cannot_access(self):
        self.finish_event()
        for user in (self.teacher, self.advisor, self.student):
            self.client.force_authenticate(user)
            self.assertEqual(self.client.get(self.report_url()).status_code, status.HTTP_403_FORBIDDEN)
            self.assertEqual(self.client.get(self.status_url()).status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_and_manager_download_after_release(self):
        from core.user.infra.user_django_app.models import Class, UserClass

        self.finish_event()
        work = self.create_work("Trabalho do relatorio")
        self.grade_by_advisor(work, self.student)
        self.grade_by_evaluator(work)
        UserClass.objects.create(
            class_name=Class.objects.create(name="3info9"), user=self.student, year=self.edition.year
        )

        for user in (self.admin, self.manager):
            self.client.force_authenticate(user)
            response = self.client.get(self.report_url())
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIn("application/pdf", response["Content-Type"])
