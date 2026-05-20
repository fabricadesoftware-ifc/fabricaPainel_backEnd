from datetime import date, datetime

from django.test import SimpleTestCase, TestCase

from core.edition.domain.validations import validate_dates, validate_evaluation_criteria
from core.edition.infra.edition_django_app.serializers import EditionWriteSerializer
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
