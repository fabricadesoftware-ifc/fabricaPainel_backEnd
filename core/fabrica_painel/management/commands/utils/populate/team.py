from faker import Faker

from core.fabrica_painel.models import Team

from .providers import students_provider, works_provider


def create_team(basic_configs: dict, **options):
    print("Creating instances for the 'Team' model")
    print(f"{basic_configs = }")
    print(f"{options = }")

    faker_gen: Faker = basic_configs["generator"]
    faker_gen.add_provider(students_provider)
    faker_gen.add_provider(works_provider)

    for _ in range(basic_configs["instances_created"]):
        Team.objects.get_or_create(
            team_student=faker_gen.unique.painel_students(),
            work=faker_gen.unique.painel_works(),
        )
