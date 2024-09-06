from faker.providers import DynamicProvider

from core.work.infra.work_django_app.models import Field

fields_provider = DynamicProvider(
    provider_name="painel_fields",
    elements=list(Field.objects.all()),
)
