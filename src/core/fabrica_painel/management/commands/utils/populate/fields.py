from django.core.management.base import BaseCommand
from faker import Faker

from core.fabrica_painel.models import Field


def create_field(basic_configs: dict, **options):
    print("Creating instances for the 'Field' model")
    print(f"{basic_configs = }")
    print(f"{options = }")

    faker_gen: Faker = basic_configs["generator"]

    for _ in range(basic_configs["instances_created"]):
        Field.objects.get_or_create(name=faker_gen.unique.bs())
