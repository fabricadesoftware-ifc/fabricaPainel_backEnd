import random

from django.utils import timezone
from faker import Faker

from core.fabrica_painel.models import Assessment

from .providers import evaluators_provider, users_provider, works_provider


def create_assessment(basic_configs: dict, **options):
    print("Creating instances for the 'Assessment' model")
    print(f"{basic_configs = }")
    print(f"{options = }")

    faker_gen: Faker = basic_configs["generator"]
    faker_gen.add_provider(evaluators_provider)
    faker_gen.add_provider(users_provider)
    faker_gen.add_provider(works_provider)

    for _ in range(basic_configs["instances_created"]):
        Assessment.objects.get_or_create(
            registration=faker_gen.unique.painel_users(),
            work=faker_gen.unique.painel_works(),
            grade=round(
                random.uniform(options["min_grade"], options["max_grade"]), 2),
            evaluator=faker_gen.painel_evaluators(),
            date_time=timezone.now(),
        )
