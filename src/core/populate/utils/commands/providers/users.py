from faker.providers import DynamicProvider

from core.user.models import User

advisors_provider = DynamicProvider(
    provider_name="painel_advisors",
    elements=list(User.objects.filter(is_advisor=True)),
)

evaluators_provider = DynamicProvider(
    provider_name="painel_evaluators",
    elements=list(User.objects.filter(is_evaluator=True)),
)

students_provider = DynamicProvider(
    provider_name="painel_students",
    elements=list(User.objects.filter(user_type="STUDENT")),
)

users_provider = DynamicProvider(
    provider_name="painel_users",
    elements=list(User.objects.all()),
)
