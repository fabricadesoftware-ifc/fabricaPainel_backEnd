from faker.providers import DynamicProvider

from core.edition.infra.edition_django_app.models import Edition

editions_provider = DynamicProvider(
    provider_name="painel_editions",
    elements=list(Edition.objects.all()),
)
