from faker.providers import DynamicProvider

from core.usuario.models import Usuario

advisors_provider = DynamicProvider(
    provider_name="painel_advisors",
    elements=list(Usuario.objects.filter(is_advisor=True)),
)

evaluators_provider = DynamicProvider(
    provider_name="painel_evaluators",
    elements=list(Usuario.objects.filter(is_evaluator=True)),
)

students_provider = DynamicProvider(
    provider_name="painel_students",
    elements=list(Usuario.objects.filter(user_type="STUDENT")),
)

users_provider = DynamicProvider(
    provider_name="painel_users",
    elements=list(Usuario.objects.all()),
)
