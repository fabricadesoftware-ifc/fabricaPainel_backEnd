from faker.providers import DynamicProvider

from core.fabrica_painel.models import Field

fields_provider = DynamicProvider(
    provider_name="painel_fields",
    elements=list(Field.objects.all()),
)
