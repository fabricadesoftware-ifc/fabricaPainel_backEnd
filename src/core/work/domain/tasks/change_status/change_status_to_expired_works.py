from django.utils import timezone
from core.work.infra.work_django_app.models import Work, WorkCollaborator
from core.work.domain.value_objects import WorkStatusType, WorkAdvisorStatusType, WorkCollaboratorStatusType
from celery import shared_task

@shared_task
def change_status_to_expired():
    print("Expirando trabalhos pendentes")
    works_pending = Work.objects.filter(status__in=[WorkStatusType.Type.NEEDS_CHANGES.value, WorkStatusType.Type.PENDING.value])
    work_advisors = Work.objects.filter(advisor_status=WorkAdvisorStatusType.Type.PENDING.value)
    work_collaborators = WorkCollaborator.objects.filter(status=WorkCollaboratorStatusType.Type.PENDING.value)

    for work in works_pending:
        work.status =  WorkStatusType.Type.EXPIRED.value
        work.save()
        
    for collaborator in work_collaborators:
        collaborator.status = WorkCollaboratorStatusType.Type.EXPIRED.value
        collaborator.save()        
        
    for work in work_advisors:
        work.advisor_status = WorkAdvisorStatusType.Type.EXPIRED.value
        work.save()
    
    return 'Trabalhos expirados com sucesso'



