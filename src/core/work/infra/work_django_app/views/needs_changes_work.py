from django.utils import timezone
from datetime import datetime
from uuid import uuid4

from rest_framework.decorators import api_view, throttle_classes, permission_classes
from rest_framework.throttling import UserRateThrottle
from rest_framework.response import Response
from rest_framework import status

from core.work.domain.tasks import send_work_new_status_needs_changes_email_to_student
from core.work.domain.tasks import send_work_needs_changes_email_to_student
from django_project.permissions import IsAdvisor

from core.edition.infra.edition_django_app.models import Edition
from core.work.infra.work_django_app.models import Work, WorkStatusType


@api_view(["GET"])
@throttle_classes([UserRateThrottle])
@permission_classes([IsAdvisor])
def needs_changes_work(request, *args, **kwargs) -> Response:
    message = request.query_params.get("message", None)
    
    try:
        work = Work.objects.get(pk=kwargs["pk"])
        
    except Work.DoesNotExist:
        return Response(
            {"error": "Trabalho não encontrado."},
            status=status.HTTP_404_NOT_FOUND,
        )
    token = uuid4()
    edition = Edition.objects.get(id=work.edition.id)

    student = work.team.team_members
    students_ids = []
    for s in student.all():
        students_ids.append(s.id)

    if work.final_submission_work_date is not None and work.verification_token is None and edition.final_advisor_date > datetime.now().date():
        work.final_submission_work_date = None
        work.verification_token = token
        work.status = WorkStatusType.Type.NEEDS_CHANGES.value
        work.needs_changes_submission_work_date = timezone.now()
        work.save()
        
        send_work_new_status_needs_changes_email_to_student.delay(students_ids, message, work.title)
        return Response(
            {"message": "O Trabalho que estava aceito precisa de madanças."},
            status=status.HTTP_200_OK,
        )
    elif edition.final_advisor_date > datetime.now().date():
        work.status = WorkStatusType.Type.NEEDS_CHANGES.value
        work.needs_changes_submission_work_date = timezone.now()
        work.save()
        
        send_work_needs_changes_email_to_student.delay(students_ids, message, work.title)
        return Response(
            {"message": "O Trabalho precisa de mudanças."},
            status=status.HTTP_200_OK,
        )

