from faker.providers import DynamicProvider

from core.work.infra.work_django_app.models import Work

works_provider = DynamicProvider(
    provider_name="painel_works",
    elements=list(Work.objects.all()),
)
