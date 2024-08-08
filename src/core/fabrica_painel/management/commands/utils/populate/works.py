from faker import Faker

from core.fabrica_painel.models import Work

from .providers import advisors_provider, editions_provider, fields_provider


def create_work(basic_configs: dict, **options):
    print("Creating instances for the 'Work' model")
    print(f"{basic_configs = }")
    print(f"{options = }")

    faker_gen: Faker = basic_configs["generator"]
    faker_gen.add_provider(advisors_provider)
    faker_gen.add_provider(editions_provider)
    faker_gen.add_provider(fields_provider)

    for _ in range(basic_configs["instances_created"]):
        Work.objects.get_or_create(
            title=faker_gen.sentence(),
            abstract=faker_gen.paragraph(),
            advisor=faker_gen.painel_advisors(),
            edition=faker_gen.unique.painel_editions(),
            field=faker_gen.unique.painel_fields(),
        )
