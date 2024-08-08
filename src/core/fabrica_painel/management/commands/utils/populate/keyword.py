from faker import Faker

from core.fabrica_painel.models import Keyword

from .providers import works_provider


def create_keyword(basic_configs: dict, **options):
    print("Creating instances for the 'Keyword' model")
    print(f"{basic_configs = }")
    print(f"{options = }")

    faker_gen: Faker = basic_configs["generator"]
    faker_gen.add_provider(works_provider)

    for _ in range(basic_configs["instances_created"]):
        Keyword.objects.get_or_create(
            name=faker_gen.unique.sentence(),
            work=faker_gen.painel_works(),
        )
