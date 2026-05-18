from datetime import date

from django.test import SimpleTestCase

from core.edition.domain.validations import validate_dates


class ValidateEditionDatesTestCase(SimpleTestCase):
    def valid_attrs(self):
        return {
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

    def test_still_rejects_invalid_advisor_acceptance_period(self):
        attrs = self.valid_attrs()
        attrs["initial_advisor_acceptance"] = date(2026, 8, 13)

        with self.assertRaises(ValueError):
            validate_dates(attrs)

    def test_still_rejects_first_advisor_period_after_second_submission_start(self):
        attrs = self.valid_attrs()
        attrs["final_advisor_acceptance"] = date(2026, 8, 16)

        with self.assertRaises(ValueError):
            validate_dates(attrs)
