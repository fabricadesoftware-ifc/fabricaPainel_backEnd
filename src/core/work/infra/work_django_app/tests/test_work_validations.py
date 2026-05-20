from datetime import timedelta

from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from core.cross_cutting_themes.infra.cross_cutting_themes_django_app.models import CrossCuttingTheme
from core.edition.infra.edition_django_app.models import Edition
from core.field.infra.field_django_app.models import Field
from core.user.domain.value_objects import UserType
from core.user.infra.user_django_app.models import Class, User, UserClass
from core.work.infra.work_django_app.models import Ods, Team, Work


class WorkValidationApiTest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.today = timezone.localdate()
        self.password = "test-password-123"
        self.registration = 2026002000

        self.student = self.create_user("student.work@test.local", UserType.Type.STUDENT.value)
        self.student_two = self.create_user("student2.work@test.local", UserType.Type.STUDENT.value)
        self.teacher = self.create_user("teacher.work@test.local", UserType.Type.TEACHER.value)
        self.advisor = self.create_user(
            "advisor.work@test.local",
            UserType.Type.TEACHER.value,
            is_advisor=True,
        )
        self.collaborator = self.create_user(
            "collaborator.work@test.local",
            UserType.Type.TEACHER.value,
            is_collaborator=True,
        )
        self.collaborator_two = self.create_user(
            "collaborator2.work@test.local",
            UserType.Type.TEACHER.value,
            is_collaborator=True,
        )

        self.field = Field.objects.create(name="Work Validation Field")
        self.theme = CrossCuttingTheme.objects.create(name="Work Validation Theme")
        self.ods = Ods.objects.create(name="Work Validation ODS")

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

    def create_edition(self, *, submission_open=True, members_min=2, members_max=4, collaborators_max=2):
        if submission_open:
            initial_submission_date = self.today - timedelta(days=1)
            final_submission_date = self.today + timedelta(days=1)
        else:
            initial_submission_date = self.today - timedelta(days=10)
            final_submission_date = self.today - timedelta(days=8)

        return Edition.objects.create(
            year=self.today.year,
            theme="Work Validation Theme",
            edition_name="Work Validation Edition",
            event_date=self.today + timedelta(days=5),
            final_event_date=self.today + timedelta(days=6),
            initial_submission_date=initial_submission_date,
            final_submission_date=final_submission_date,
            initial_second_submission_date=self.today + timedelta(days=2),
            final_second_submission_date=self.today + timedelta(days=3),
            initial_advisor_acceptance=self.today - timedelta(days=1),
            final_advisor_acceptance=self.today + timedelta(days=2),
            initial_second_advisor_date=self.today + timedelta(days=2),
            final_second_advisor_date=self.today + timedelta(days=3),
            initial_evaluators_date=self.today + timedelta(days=5),
            final_evaluators_date=self.today + timedelta(days=7),
            members_min=members_min,
            members_max=members_max,
            collaborators_min=0,
            collaborators_max=collaborators_max,
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

    def create_team(self, edition, members=None):
        team = Team.objects.create(edition=edition)
        team.team_members.set(members or [self.student, self.student_two])
        return team

    def work_payload(self, edition, team, extra=None):
        payload = {
            "title": "Work Validation Submission",
            "abstract": "Resumo com palavras suficientes para validacao.",
            "edition": edition.id,
            "field": [self.field.id],
            "advisor": self.advisor.id,
            "cross_cutting_theme": self.theme.id,
            "team": team.id,
            "ods": [self.ods.id],
            "collaborators": [],
            "integrated_project": False,
        }
        payload.update(extra or {})
        return payload

    def assert_response_contains(self, response, text):
        self.assertIn(text, str(response.data))

    def test_rejects_team_with_fewer_members_than_edition_minimum(self):
        edition = self.create_edition(members_min=2)
        self.client.force_authenticate(self.student)

        response = self.client.post(
            "/api/team/",
            {"team_members": [self.student.id], "edition": edition.id},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.data)
        self.assert_response_contains(response, "mínimo 2")
        self.assertFalse(Team.objects.exists())

    def test_rejects_team_with_non_student_member(self):
        edition = self.create_edition(members_min=1)
        self.client.force_authenticate(self.student)

        response = self.client.post(
            "/api/team/",
            {"team_members": [self.teacher.id], "edition": edition.id},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.data)
        self.assert_response_contains(response, "não é estudante")
        self.assertFalse(Team.objects.exists())

    def test_rejects_work_submission_outside_submission_period(self):
        edition = self.create_edition(submission_open=False)
        team = self.create_team(edition)
        self.client.force_authenticate(self.student)

        response = self.client.post(
            "/api/work/",
            self.work_payload(edition, team),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.data)
        self.assert_response_contains(response, "Fora da data")
        self.assertFalse(Work.objects.exists())

    def test_rejects_integrated_project_when_students_are_from_different_classes(self):
        edition = self.create_edition()
        class_a = Class.objects.create(name="1INFO1")
        class_b = Class.objects.create(name="2INFO1")
        UserClass.objects.create(user=self.student, class_name=class_a, year=edition.year)
        UserClass.objects.create(user=self.student_two, class_name=class_b, year=edition.year)
        team = self.create_team(edition)
        self.client.force_authenticate(self.student)

        response = self.client.post(
            "/api/work/",
            self.work_payload(edition, team, {"integrated_project": True}),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.data)
        self.assert_response_contains(response, "mesma turma")
        self.assertFalse(Work.objects.exists())

    def test_rejects_more_collaborators_than_edition_allows(self):
        edition = self.create_edition(collaborators_max=1)
        team = self.create_team(edition)
        self.client.force_authenticate(self.student)

        response = self.client.post(
            "/api/work/",
            self.work_payload(
                edition,
                team,
                {"collaborators": [self.collaborator.id, self.collaborator_two.id]},
            ),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.data)
        self.assert_response_contains(response, "maximo 1 colaboradores")
        self.assertFalse(Work.objects.exists())
