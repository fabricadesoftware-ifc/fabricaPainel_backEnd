from django.utils import timezone
from core.work.infra.work_django_app.models import Work
from core.work.domain.value_objects import WorkStatusType
from celery import shared_task

@shared_task
def change_status_to_expired():
    print("Expirando trabalhos pendentes")
    works = Work.objects.filter(status=WorkStatusType.Type.PENDING.value)
    for work in works:
        work.status = WorkStatusType.Type.EXPIRED.value
        work.save()
    
    return 'Trabalhos expirados com sucesso'



