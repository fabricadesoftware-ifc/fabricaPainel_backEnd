from random import randint

from django.utils import timezone
from faker import Faker

from core.fabrica_painel.models import Assessment

from .providers import evaluators_provider, works_provider


def create_assessment(basic_configs: dict, **options):
    # raise NotImplementedError("WIP - The dev didn't understand the 'assessment' model :)")

    print("Creating instances for the 'Assessment' model")
    print(f"{basic_configs = }")
    print(f"{options = }")

    faker_gen: Faker = basic_configs["generator"]
    faker_gen.add_provider(evaluators_provider)
    faker_gen.add_provider(works_provider)

    for _ in range(basic_configs["instances_created"]):
        Assessment.objects.get_or_create(
            registration=faker_gen.unique.,
            work=faker_gen.unique.painel_works(),
            grade=randint(options["min_grade"], options["max_grade"]),
            evaluator=faker_gen.painel_evaluators(),
            date_time=timezone.now()
        )
