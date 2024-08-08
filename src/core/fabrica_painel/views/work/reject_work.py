import os 
from django.utils import timezone
from dotenv import load_dotenv
from uuid import uuid4

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from core.fabrica_painel.tasks.send_email_student import send_work_new_status_reject_email_to_student
from core.fabrica_painel.tasks.send_email_student import send_work_reject_email_to_student

from core.fabrica_painel.models import Edition
from core.fabrica_painel.models import Work

load_dotenv()

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

    student = work.team.team_student
    student_id = student.id

    if work.final_submission_work_date is not None and work.verification_token is None and edition.final_advisor_date > timezone.now():
        work.final_submission_work_date = None
        work.verification_token = token
        work.status = Work.WorkStatus.REJECTED
        work.reject_submission_work_date = timezone.now()
        work.save()
    
        send_work_new_status_reject_email_to_student.delay(student_id)
        return Response(
            {"message": "O Trabalho que estava aceito foi rejeitado."},
            status=status.HTTP_200_OK,
        )
    elif edition.final_advisor_date > timezone.now():
        work.status = Work.WorkStatus.REJECTED
        work.reject_submission_work_date = timezone.now()
        work.save()
        send_work_reject_email_to_student.delay(student_id)
        return Response(
            {"message": "O Trabalho foi rejeitado."},
            status=status.HTTP_200_OK,
        )

