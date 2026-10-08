from datetime import date, datetime, time

from django.test import SimpleTestCase, TestCase
from rest_framework import status
from rest_framework.test import APIClient, APITestCase
from django.utils import timezone

from core.edition.domain.validations import validate_dates, validate_evaluation_criteria
from core.edition.infra.edition_django_app.models import Edition, EvaluationDailyWindow
from core.edition.infra.edition_django_app.serializers import EditionWriteSerializer
from core.user.domain.value_objects import UserType
from core.user.infra.user_django_app.models import User
from core.uploader.infra.uploader_django_app.models import Image


class ValidateEditionDatesTestCase(SimpleTestCase):
    def valid_attrs(self):
        return {
            "event_date": date(2026, 8, 23),
            "final_event_date": date(2026, 8, 29),
            "initial_submission_date": date(2026, 8, 1),
            "final_submission_date": date(2026, 8, 10),
            "initial_advisor_acceptance": date(2026, 8, 5),
            "final_advisor_acceptance": date(2026, 8, 12),
            "initial_second_submission_date": date(2026, 8, 15),
            "final_second_submission_date": date(2026, 8, 20),
            "initial_second_advisor_date": date(2026, 8, 18),
            "final_second_advisor_date": date(2026, 8, 22),
            "initial_evaluators_date": date(2026, 8, 23),
            "final_evaluators_date": date(2026, 8, 30),
        }

    def test_allows_submission_and_advisor_acceptance_overlap(self):
        self.assertFalse(validate_dates(self.valid_attrs()))

    def test_accepts_commission_schedule_with_acceptance_after_submission(self):
        attrs = {
            "initial_submission_date": date(2026, 8, 3),
            "final_submission_date": date(2026, 8, 17),
            "initial_advisor_acceptance": date(2026, 8, 18),
            "final_advisor_acceptance": date(2026, 8, 24),
            "initial_second_submission_date": date(2026, 8, 25),
            "final_second_submission_date": date(2026, 9, 4),
            "initial_second_advisor_date": date(2026, 9, 8),
            "final_second_advisor_date": date(2026, 9, 14),
            "event_date": date(2026, 10, 8),
            "final_event_date": date(2026, 10, 9),
            "initial_evaluators_date": date(2026, 10, 8),
            "final_evaluators_date": date(2026, 10, 9),
        }

        self.assertFalse(validate_dates(attrs))

    def test_allows_evaluation_to_end_after_event(self):
        attrs = self.valid_attrs()
        attrs["final_event_date"] = date(2026, 8, 24)
        attrs["final_evaluators_date"] = date(2026, 8, 30)

        self.assertFalse(validate_dates(attrs))

    def test_still_rejects_invalid_advisor_acceptance_period(self):
        attrs = self.valid_attrs()
        attrs["initial_advisor_acceptance"] = date(2026, 8, 13)

        with self.assertRaises(ValueError):
            validate_dates(attrs)

    def test_rejects_evaluation_before_event(self):
        attrs = self.valid_attrs()
        attrs["initial_evaluators_date"] = date(2026, 8, 22)

        with self.assertRaises(ValueError):
            validate_dates(attrs)

    def test_rejects_evaluation_start_after_event(self):
        attrs = self.valid_attrs()
        attrs["initial_evaluators_date"] = date(2026, 8, 30)
        attrs["final_evaluators_date"] = date(2026, 8, 31)

        with self.assertRaises(ValueError):
            validate_dates(attrs)

    def test_still_rejects_first_advisor_period_after_second_submission_start(self):
        attrs = self.valid_attrs()
        attrs["final_advisor_acceptance"] = date(2026, 8, 16)

        with self.assertRaises(ValueError):
            validate_dates(attrs)


class ValidateEditionEvaluationCriteriaTestCase(SimpleTestCase):
    def valid_criteria(self):
        return [
            {
                "key": "work",
                "target": "work",
                "label": "Nota do avaliador",
                "weight": 70,
                "criteria": [
                    {"key": "presentation", "label": "Apresentacao", "weight": 40},
                    {"key": "content", "label": "Conteudo", "weight": 60},
                ],
            },
            {
                "key": "student",
                "target": "student",
                "label": "Nota do orientador",
                "weight": 30,
                "criteria": [
                    {"key": "participation", "label": "Participacao", "weight": 100},
                ],
            },
        ]

    def test_accepts_evaluation_criteria_when_totals_are_100(self):
        criteria = validate_evaluation_criteria(self.valid_criteria())

        self.assertEqual(criteria[0]["weight"], 70.0)
        self.assertEqual(criteria[0]["criteria"][0]["weight"], 40.0)

    def test_rejects_evaluation_criteria_when_group_total_is_not_100(self):
        criteria = self.valid_criteria()
        criteria[1]["weight"] = 20

        with self.assertRaises(ValueError):
            validate_evaluation_criteria(criteria)

    def test_rejects_evaluation_criteria_when_internal_total_is_not_100(self):
        criteria = self.valid_criteria()
        criteria[0]["criteria"][1]["weight"] = 50

        with self.assertRaises(ValueError):
            validate_evaluation_criteria(criteria)

    def test_rejects_duplicate_evaluation_targets(self):
        criteria = self.valid_criteria()
        criteria[1]["target"] = "work"

        with self.assertRaises(ValueError):
            validate_evaluation_criteria(criteria)

    def test_rejects_missing_evaluation_target(self):
        criteria = self.valid_criteria()
        criteria.pop()
        criteria[0]["weight"] = 100

        with self.assertRaises(ValueError):
            validate_evaluation_criteria(criteria)

    def test_accepts_default_evaluation_criteria(self):
        criteria = validate_evaluation_criteria(None)

        self.assertEqual(criteria[0]["target"], "work")
        self.assertEqual(criteria[1]["target"], "student")


class EditionWriteSerializerTestCase(TestCase):
    def valid_payload(self):
        year = datetime.now().year
        return {
            "edition_name": "Edicao Teste",
            "year": year,
            "theme": "Tema Teste",
            "event_date": date(year, 8, 23),
            "final_event_date": date(year, 8, 24),
            "initial_submission_date": date(year, 8, 1),
            "final_submission_date": date(year, 8, 10),
            "initial_advisor_acceptance": date(year, 8, 1),
            "final_advisor_acceptance": date(year, 8, 12),
            "initial_second_submission_date": date(year, 8, 15),
            "final_second_submission_date": date(year, 8, 20),
            "initial_second_advisor_date": date(year, 8, 15),
            "final_second_advisor_date": date(year, 8, 22),
            "initial_evaluators_date": date(year, 8, 23),
            "final_evaluators_date": date(year, 8, 30),
            "members_min": 2,
            "members_max": 5,
            "collaborators_min": 1,
            "collaborators_max": 3,
            "subjects_min": 1,
            "subjects_max": 3,
            "evaluators_count": 1,
            "works_per_evaluator_max": 10,
            "works_per_collaborator_max": 10,
            "works_per_advisor_max": 10,
            "words_per_work_min": 200,
            "words_per_work_max": 500,
            "workload": 60,
            "evaluation_criteria": [
                {
                    "key": "work",
                    "target": "work",
                    "label": "Nota do avaliador",
                    "weight": 70,
                    "criteria": [
                        {"key": "work_general", "label": "Nota geral do trabalho", "weight": 70},
                        {"key": "presentation", "label": "Nota de apresentacao", "weight": 30},
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
        }

    def test_accepts_banner_attachment_key(self):
        image = Image.objects.create(description="Banner")
        payload = self.valid_payload()
        payload["banner"] = str(image.attachment_key)

        serializer = EditionWriteSerializer(
            data=payload,
            context={"request": type("Request", (), {"method": "POST"})()},
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        edition = serializer.save()

        self.assertEqual(edition.banner_id, image.id)


class EvaluatorWindowStatusTestCase(TestCase):
    def create_edition(self):
        return Edition.objects.create(
            year=2026,
            theme="Tema",
            edition_name="Edicao Janela",
            workload=10,
        )

    def test_returns_none_when_edition_has_no_windows_configured(self):
        edition = self.create_edition()

        self.assertIsNone(edition.evaluator_window_status())

    def test_is_open_now_when_current_time_is_inside_todays_window(self):
        edition = self.create_edition()
        now = timezone.make_aware(datetime(2026, 10, 9, 15, 0))
        EvaluationDailyWindow.objects.create(
            edition=edition, date=now.date(), opens_at=time(8, 0), closes_at=time(22, 0)
        )

        status = edition.evaluator_window_status(now=now)

        self.assertTrue(status["is_open_now"])
        self.assertIsNone(status["next_open_at"])

    def test_shows_reopen_time_later_today_when_closed_before_opening(self):
        edition = self.create_edition()
        now = timezone.make_aware(datetime(2026, 10, 9, 7, 0))
        EvaluationDailyWindow.objects.create(
            edition=edition, date=now.date(), opens_at=time(10, 0), closes_at=time(22, 0)
        )

        status = edition.evaluator_window_status(now=now)

        self.assertFalse(status["is_open_now"])
        self.assertEqual(status["next_open_at"], timezone.make_aware(datetime(2026, 10, 9, 10, 0)))

    def test_shows_next_days_reopen_time_after_todays_window_closed(self):
        edition = self.create_edition()
        now = timezone.make_aware(datetime(2026, 10, 9, 23, 0))
        EvaluationDailyWindow.objects.create(
            edition=edition, date=date(2026, 10, 9), opens_at=time(8, 0), closes_at=time(22, 0)
        )
        EvaluationDailyWindow.objects.create(
            edition=edition, date=date(2026, 10, 10), opens_at=time(9, 0), closes_at=time(20, 0)
        )

        status = edition.evaluator_window_status(now=now)

        self.assertFalse(status["is_open_now"])
        self.assertEqual(status["next_open_at"], timezone.make_aware(datetime(2026, 10, 10, 9, 0)))

    def test_shows_next_configured_day_when_today_has_no_window(self):
        edition = self.create_edition()
        now = timezone.make_aware(datetime(2026, 10, 9, 12, 0))
        EvaluationDailyWindow.objects.create(
            edition=edition, date=date(2026, 10, 11), opens_at=time(9, 0), closes_at=time(20, 0)
        )

        status = edition.evaluator_window_status(now=now)

        self.assertFalse(status["is_open_now"])
        self.assertEqual(status["next_open_at"], timezone.make_aware(datetime(2026, 10, 11, 9, 0)))


class EditionWritePermissionTestCase(APITestCase):
    """Todo usuario autenticado le edicoes; criar/editar so admin ou gestao
    (professor com is_management, que continua professor no painel)."""

    def setUp(self):
        self.client = APIClient()
        self.registration = 2026030000
        self.admin = self.make_user("admin.edition@test.local", UserType.Type.ADMIN.value)
        self.manager = self.make_user(
            "manager.edition@test.local", UserType.Type.TEACHER.value, is_management=True
        )
        self.teacher = self.make_user("teacher.edition@test.local", UserType.Type.TEACHER.value)
        self.student = self.make_user("student.edition@test.local", UserType.Type.STUDENT.value)
        self.edition = Edition.objects.create(
            year=2026, theme="Tema", edition_name="Edicao permissao", workload=10
        )

    def make_user(self, email, user_type, **flags):
        self.registration += 1
        user = User.objects.create_user(
            email=email, password="test-password-123", name=email.split("@")[0], registration=self.registration
        )
        user.user_type = user_type
        for field, value in flags.items():
            setattr(user, field, value)
        user.save()
        return user

    def test_any_authenticated_user_can_read_editions(self):
        for user in (self.admin, self.manager, self.teacher, self.student):
            self.client.force_authenticate(user)
            self.assertEqual(self.client.get("/api/edition/").status_code, status.HTTP_200_OK)

    def test_anonymous_cannot_read_editions(self):
        self.client.force_authenticate(None)
        self.assertIn(
            self.client.get("/api/edition/").status_code,
            (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN),
        )

    def test_admin_and_management_can_edit_edition(self):
        for index, user in enumerate((self.admin, self.manager)):
            self.client.force_authenticate(user)
            response = self.client.patch(
                f"/api/edition/{self.edition.id}/", {"theme": f"Novo tema {index}"}, format="json"
            )

            self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
            self.edition.refresh_from_db()
            self.assertEqual(self.edition.theme, f"Novo tema {index}")

    def test_plain_teacher_and_student_cannot_edit_edition(self):
        for user in (self.teacher, self.student):
            self.client.force_authenticate(user)
            response = self.client.patch(
                f"/api/edition/{self.edition.id}/", {"theme": "Invasao"}, format="json"
            )

            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
            self.edition.refresh_from_db()
            self.assertEqual(self.edition.theme, "Tema")

    def test_management_passes_create_permission_but_plain_teacher_does_not(self):
        self.client.force_authenticate(self.teacher)
        self.assertEqual(self.client.post("/api/edition/", {}, format="json").status_code, status.HTTP_403_FORBIDDEN)

        # Gestao passa da permissao (o corpo vazio so falha na validacao, nao com 403).
        self.client.force_authenticate(self.manager)
        self.assertNotEqual(self.client.post("/api/edition/", {}, format="json").status_code, status.HTTP_403_FORBIDDEN)

