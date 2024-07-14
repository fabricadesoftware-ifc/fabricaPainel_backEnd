from faker.providers import DynamicProvider

from core.fabrica_painel.models import Work

works_provider = DynamicProvider(
    provider_name="painel_works",
    elements=list(Work.objects.all()),
)
