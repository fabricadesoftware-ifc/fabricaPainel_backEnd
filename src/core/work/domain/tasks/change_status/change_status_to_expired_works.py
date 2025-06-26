from django.utils import timezone
from core.work.infra.work_django_app.models import Work, WorkCollaborator
from core.work.domain.value_objects import WorkStatusType, WorkAdvisorStatusType, WorkCollaboratorStatusType
from celery import shared_task

@shared_task
def change_status_to_expired():
    print("Expirando trabalhos pendentes")
    works_pending = Work.objects.filter(advisor_status=WorkAdvisorStatusType.Type.PENDING.value)
    works_rejected = Work.objects.filter(advisor_status=WorkAdvisorStatusType.Type.REJECTED.value)
    
    for work in works_pending:
        work.status = WorkStatusType.Type.EXPIRED.value
        work.advisor_status = WorkAdvisorStatusType.Type.EXPIRED.value
        work.save()
        work_collaborators = WorkCollaborator.objects.filter(work=work, status=WorkCollaboratorStatusType.Type.PENDING.value)
        if work_collaborators.exists():
            for collaborator in work_collaborators:
                collaborator.status = WorkCollaboratorStatusType.Type.EXPIRED.value
                collaborator.save()
    
    for work in works_rejected:
        work.status = WorkStatusType.Type.REJECTED.value
        work.save()
        work_collaborators = WorkCollaborator.objects.filter(work=work, status=WorkCollaboratorStatusType.Type.PENDING.value)
        if work_collaborators.exists():
            for collaborator in work_collaborators:
                collaborator.status = WorkCollaboratorStatusType.Type.EXPIRED.value
                collaborator.save()
    return 'Trabalhos expirados com sucesso'



