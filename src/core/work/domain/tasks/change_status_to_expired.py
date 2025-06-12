from django.utils import timezone
from core.work.infra.work_django_app.models import Work
from celery import shared_task

@shared_task
def change_status_to_expired():
    print("Expirando trabalhos pendentes")
    works = Work.objects.filter(status=Work.Status.PENDING)
    for work in works:
        work.status = Work.Status.EXPIRED
        work.save()
    
    return 'Trabalhos expirados com sucesso'



