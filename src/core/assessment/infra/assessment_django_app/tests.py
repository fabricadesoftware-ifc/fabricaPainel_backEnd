from datetime import timedelta
from decimal import Decimal

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


class AssessmentValidationApiTest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.today = timezone.localdate()
        self.password = "test-password-123"
        self.registration = 2026001000

        self.student = self.create_user("student.assessment@test.local", UserType.Type.STUDENT.value)
        self.student_two = self.create_user("student2.assessment@test.local", UserType.Type.STUDENT.value)
        self.student_outside_team = self.create_user("student3.assessment@test.local", UserType.Type.STUDENT.value)
        self.advisor = self.create_user(
            "advisor.assessment@test.local",
            UserType.Type.TEACHER.value,
            is_advisor=True,
        )
        self.other_teacher = self.create_user(
            "other.teacher.assessment@test.local",
            UserType.Type.TEACHER.value,
            is_advisor=True,
        )
        self.evaluator_user = self.create_user("evaluator.assessment@test.local", UserType.Type.TEACHER.value)
        self.other_evaluator_user = self.create_user(
            "other.evaluator.assessment@test.local",
            UserType.Type.TEACHER.value,
        )
        self.evaluator = Evaluator.objects.create(user=self.evaluator_user)
        self.other_evaluator = Evaluator.objects.create(user=self.other_evaluator_user)

        self.field = Field.objects.create(name="Assessment Field")
        self.theme = CrossCuttingTheme.objects.create(name="Assessment Theme")
        self.ods = Ods.objects.create(name="Assessment ODS")

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

    def create_edition(self, *, grade_period_open=True):
        if grade_period_open:
            initial_evaluators_date = self.today - timedelta(days=1)
            final_evaluators_date = self.today + timedelta(days=1)
        else:
            initial_evaluators_date = self.today + timedelta(days=2)
            final_evaluators_date = self.today + timedelta(days=4)

        return Edition.objects.create(
            year=self.today.year,
            theme="Assessment Theme",
            edition_name="Assessment Edition",
            event_date=self.today,
            final_event_date=self.today + timedelta(days=2),
            initial_submission_date=self.today - timedelta(days=10),
            final_submission_date=self.today - timedelta(days=8),
            initial_second_submission_date=self.today - timedelta(days=7),
            final_second_submission_date=self.today - timedelta(days=6),
            initial_advisor_acceptance=self.today - timedelta(days=10),
            final_advisor_acceptance=self.today - timedelta(days=8),
            initial_second_advisor_date=self.today - timedelta(days=7),
            final_second_advisor_date=self.today - timedelta(days=6),
            initial_evaluators_date=initial_evaluators_date,
            final_evaluators_date=final_evaluators_date,
            members_min=2,
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
            evaluation_criteria=[
                {
                    "key": "work",
                    "target": "work",
                    "label": "Nota do avaliador",
                    "weight": 70,
                    "criteria": [
                        {"key": "work_general", "label": "Nota geral", "weight": 60},
                        {"key": "presentation", "label": "Apresentacao", "weight": 40},
                    ],
                },
                {
                    "key": "student",
                    "target": "student",
                    "label": "Nota do orientador",
                    "weight": 30,
                    "criteria": [
                        {"key": "student_general", "label": "Nota geral do aluno", "weight": 100},
                    ],
                },
            ],
        )

    def create_work(self, *, grade_period_open=True, assign_evaluator=True):
        edition = self.create_edition(grade_period_open=grade_period_open)
        team = Team.objects.create(edition=edition)
        team.team_members.set([self.student, self.student_two])

        work = Work.objects.create(
            title="Assessment Validation Work",
            abstract="Resumo de validacao de avaliacao.",
            edition=edition,
            cross_cutting_theme=self.theme,
            team=team,
            advisor=self.advisor,
            advisor_status=WorkAdvisorStatusType.Type.APPROVED.value,
            status=WorkStatusType.Type.APPROVED.value,
            integrated_project=False,
        )
        work.field.set([self.field])
        work.ods.set([self.ods])
        if assign_evaluator:
            work.evaluator.set([self.evaluator])
        return work

    def post_work_assessment(self, work, payload=None, user=None):
        self.client.force_authenticate(user or self.evaluator_user)
        data = {
            "evaluator": self.evaluator.id,
            "work": str(work.id),
            "grade": "8.00",
            "date_time": timezone.now().isoformat(),
            "committee_feedback": "Avaliacao de teste.",
        }
        data.update(payload or {})
        return self.client.post("/api/assessment/", data, format="json")

    def post_student_assessment(self, work, payload=None, user=None):
        self.client.force_authenticate(user or self.advisor)
        data = {
            "student": self.student.id,
            "work": str(work.id),
            "grade": "8.00",
            "date_time": timezone.now().isoformat(),
        }
        data.update(payload or {})
        return self.client.post("/api/student-assessments/", data, format="json")

    def assert_response_contains(self, response, text):
        self.assertIn(text, str(response.data))

    def test_rejects_work_assessment_before_grade_period(self):
        work = self.create_work(grade_period_open=False)

        response = self.post_work_assessment(work)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.data)
        self.assert_response_contains(response, "Avaliacoes so podem ser realizadas")
        self.assertFalse(Assessment.objects.exists())

    def test_rejects_student_assessment_before_grade_period(self):
        work = self.create_work(grade_period_open=False)

        response = self.post_student_assessment(work)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.data)
        self.assert_response_contains(response, "Avaliacoes so podem ser realizadas")
        self.assertFalse(StudentAssessments.objects.exists())

    def test_rejects_work_assessment_when_evaluator_is_not_assigned_to_work(self):
        work = self.create_work(assign_evaluator=False)

        response = self.post_work_assessment(work)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.data)
        self.assert_response_contains(response, "avaliador relacionado")
        self.assertFalse(Assessment.objects.exists())

    def test_rejects_work_assessment_when_payload_evaluator_differs_from_authenticated_user(self):
        work = self.create_work()

        response = self.post_work_assessment(work, {"evaluator": self.other_evaluator.id})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.data)
        self.assert_response_contains(response, "Só pode avaliar trabalhos")
        self.assertFalse(Assessment.objects.exists())

    def test_rejects_student_assessment_from_teacher_who_is_not_work_advisor(self):
        work = self.create_work()

        response = self.post_student_assessment(work, user=self.other_teacher)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.data)
        self.assert_response_contains(response, "orientador relacionado")
        self.assertFalse(StudentAssessments.objects.exists())

    def test_rejects_student_assessment_for_student_outside_work_team(self):
        work = self.create_work()

        response = self.post_student_assessment(work, {"student": self.student_outside_team.id})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.data)
        self.assert_response_contains(response, "membro da equipe")
        self.assertFalse(StudentAssessments.objects.exists())

    def test_rejects_duplicate_student_assessment_for_same_work_and_student(self):
        work = self.create_work()
        StudentAssessments.objects.create(
            work=work,
            student=self.student,
            grade=Decimal("8.00"),
            date_time=timezone.now(),
        )

        response = self.post_student_assessment(work)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.data)
        self.assert_response_contains(response, "Já existe uma avaliação")
        self.assertEqual(StudentAssessments.objects.count(), 1)

    def test_rejects_grade_outside_zero_to_ten_range(self):
        work = self.create_work()

        response = self.post_work_assessment(work, {"grade": "11.00"})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.data)
        self.assert_response_contains(response, "A nota deve ser entre 0 e 10")
        self.assertFalse(Assessment.objects.exists())

    def test_rejects_missing_configured_criterion_grade(self):
        work = self.create_work()

        response = self.post_work_assessment(
            work,
            {
                "criterion_grades": [
                    {"key": "work_general", "grade": "8.00"},
                ],
            },
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.data)
        self.assert_response_contains(response, "Todos os criterios configurados precisam receber nota")
        self.assertFalse(Assessment.objects.exists())

    def test_rejects_unknown_criterion_grade_key(self):
        work = self.create_work()

        response = self.post_work_assessment(
            work,
            {
                "criterion_grades": [
                    {"key": "work_general", "grade": "8.00"},
                    {"key": "unknown", "grade": "9.00"},
                ],
            },
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.data)
        self.assert_response_contains(response, "nao pertence a esta avaliacao")
        self.assertFalse(Assessment.objects.exists())

    def test_computes_weighted_grade_from_criteria(self):
        work = self.create_work()

        response = self.post_work_assessment(
            work,
            {
                "criterion_grades": [
                    {"key": "work_general", "grade": "8.00"},
                    {"key": "presentation", "grade": "10.00"},
                ],
            },
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        assessment = Assessment.objects.get(work=work, evaluator=self.evaluator)
        self.assertEqual(assessment.grade, Decimal("8.80"))
        self.assertEqual(len(assessment.criterion_grades), 2)
