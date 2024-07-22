from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from asgiref.sync import async_to_sync
from core.fabrica_painel.use_case.send_email_student.send_work_reject_email_to_student import send_work_reject_email_to_student
from core.fabrica_painel.use_case.send_email_student.send_work_new_status_reject_email_to_student import send_work_new_status_reject_email_to_student
from uuid import uuid4

from core.fabrica_painel.models.work import Work


import os 
from dotenv import load_dotenv

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
    email_student_recipient_list = [work.team]
    from_email = os.getenv("EMAIL_HOST_USER")
    token = uuid4()

    if work.final_submission_work_date is not None and work.verification_token is None:
        work.final_submission_work_date = None
        work.verification_token = token
        work.status = Work.WorkStatus.REJECTED
        work.reject_submission_work_date = timezone.now()
        work.save()
    
        async_to_sync(send_work_new_status_reject_email_to_student)(from_email, email_student_recipient_list)
        return Response(
            {"message": "O Trabalho que estava aceito foi rejeitado."},
            status=status.HTTP_200_OK,
        )
    else :
        work.status = Work.WorkStatus.REJECTED
        work.reject_submission_work_date = timezone.now()
        work.save()
        async_to_sync(send_work_reject_email_to_student)(from_email, email_student_recipient_list)
        return Response(
            {"message": "O Trabalho foi rejeitado."},
            status=status.HTTP_200_OK,
        )

