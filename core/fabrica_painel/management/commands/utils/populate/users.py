from random import choices

from faker import Faker

from core.usuario.models import Usuario

from .providers import fields_provider

# users_types = [
#     value for value, _ in Usuario.UserType.choices if value != "ADMIN"
# ]
users_types: list[str] = ["STUDENT", "TEACHER"]
users_types_weights: list[int] = [70, 30]


def create_user(basic_configs: dict, **options):
    print("Creating instances for the 'Usuario' model")
    print(f"{basic_configs = }")
    print(f"{options = }")

    faker_gen: Faker = basic_configs["generator"]
    faker_gen.add_provider(fields_provider)

    for _ in range(basic_configs["instances_created"]):
        Usuario.objects.create_user(
            email=faker_gen.email(),
            password=faker_gen.password(),
            is_advisor=faker_gen.boolean(
                chance_of_getting_true=options["advisor_chance"]
            ),
            is_evaluator=faker_gen.boolean(
                chance_of_getting_true=options["evaluator_chance"]
            ),
            # "choices" returns a list
            user_type=choices(users_types, users_types_weights, k=1)[0],
            field=faker_gen.painel_fields(),
        )
