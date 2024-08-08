from faker import Faker

from core.fabrica_painel.models import Assessments

from .providers import users_provider, works_provider


def create_assessments(basic_configs: dict, **options):
    print("Creating instances for the 'Assessments' model")
    print(f"{basic_configs = }")
    print(f"{options = }")

    faker_gen: Faker = basic_configs["generator"]
    faker_gen.add_provider(users_provider)
    faker_gen.add_provider(works_provider)

    for _ in range(basic_configs["instances_created"]):
        Assessments.objects.get_or_create(
            registration=faker_gen.unique.painel_users(),
            work=faker_gen.unique.painel_works(),
        )
