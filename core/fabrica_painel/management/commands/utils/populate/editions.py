from datetime import datetime, timedelta

from django.utils.timezone import get_default_timezone
from faker import Faker

from core.fabrica_painel.models import Edition


def create_edition(basic_configs: dict, **options):
    print("Creating instances for the 'Edition' model")
    print(f"{basic_configs = }")
    print(f"{options = }")

    faker_gen: Faker = basic_configs["generator"]
    timezone = get_default_timezone()

    for _ in range(basic_configs["instances_created"]):
        random_date: datetime = faker_gen.date_time_this_century(tzinfo=timezone)
        year: int = int(random_date.year)
        theme: str = faker_gen.unique.sentence()
        initial_submission_date: datetime = random_date + timedelta(days=1)
        final_submission_date: datetime = random_date + timedelta(days=7)
        initial_evaluators_date: datetime = random_date + timedelta(days=7 + 1)
        final_evaluators_date: datetime = random_date + timedelta(days=7 + 7)

        Edition.objects.get_or_create(
            year=year,
            theme=theme,
            edition_name=f"SEPE {year} - {theme.split(' ')[0]}",
            initil_submission_date=initial_submission_date,
            final_submission_date=final_submission_date,
            initial_advisor_date=initial_submission_date,
            final_advisor_date=final_submission_date,
            initial_evaluators_date=initial_evaluators_date,
            final_evaluators_date=final_evaluators_date,
        )
