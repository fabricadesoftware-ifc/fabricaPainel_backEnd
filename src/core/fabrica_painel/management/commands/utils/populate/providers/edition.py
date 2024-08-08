from faker.providers import DynamicProvider

from core.fabrica_painel.models import Edition

editions_provider = DynamicProvider(
    provider_name="painel_editions",
    elements=list(Edition.objects.all()),
)
