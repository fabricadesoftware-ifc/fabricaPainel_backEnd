from django.utils import timezone
from uuid import uuid4

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from core.work.domain.tasks import send_work_new_status_reject_email_to_student
from core.work.domain.tasks import send_work_reject_email_to_student

from core.edition.infra.edition_django_app.models import Edition
from core.work.infra.work_django_app.models import Work


@api_view(["GET"])
def reject_work(request, *args, **kwargs) -> Response:
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

    if work.final_submission_work_date is not None and work.verification_token is None and edition.final_advisor_date > timezone.now():
        work.final_submission_work_date = None
        work.verification_token = token
        work.status = Work.WorkStatus.REJECTED
        work.reject_submission_work_date = timezone.now()
        work.save()
    
        send_work_new_status_reject_email_to_student.delay(students_ids)
        return Response(
            {"message": "O Trabalho que estava aceito foi rejeitado."},
            status=status.HTTP_200_OK,
        )
    elif edition.final_advisor_date > timezone.now():
        work.status = Work.WorkStatus.REJECTED
        work.reject_submission_work_date = timezone.now()
        work.save()
        send_work_reject_email_to_student.delay(students_ids)
        return Response(
            {"message": "O Trabalho foi rejeitado."},
            status=status.HTTP_200_OK,
        )

