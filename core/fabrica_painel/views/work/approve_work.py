from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from asgiref.sync import async_to_sync
from core.fabrica_painel.use_case.send_email_student.send_work_approve_email_to_student import send_work_approve_email_to_student
from core.fabrica_painel.use_case.send_email_student.send_work_new_status_approve_email_to_student import send_work_new_status_approve_email_to_student

from core.fabrica_painel.models.work import Work

import os 
from dotenv import load_dotenv

load_dotenv()

@api_view(["GET"])
def approve_work(request, verification_token) -> Response:
    try:
        work = Work.objects.get(verification_token=verification_token)
    except Work.DoesNotExist:
        return Response(
            {"error": "Trabalho não encontrado."},
            status=status.HTTP_404_NOT_FOUND,
        )
    email_student_recipient_list = [work.team]
    from_email = os.getenv("EMAIL_HOST_USER")

    if work.status == Work.WorkStatus.REJECTED:
        work.final_submission_work_date = timezone.now()
        work.verification_token = None
        work.status = Work.WorkStatus.APPROVED
        work.reject_submission_work_date = None
        work.save()

        if work.final_submission_work_date is not None:
            async_to_sync(send_work_new_status_approve_email_to_student)(from_email, email_student_recipient_list)
            return Response(
        {"message": "O trabalho que tinha sido recusado foi aceito."},
        status=status.HTTP_200_OK,
        )
    else:
        work.final_submission_work_date = timezone.now()
        work.verification_token = None
        work.status = Work.WorkStatus.APPROVED
        work.save()

        if work.final_submission_work_date is not None:
            async_to_sync(send_work_approve_email_to_student)(from_email, email_student_recipient_list)
        return Response(
        {"message": "Trabalho aceito."},
        status=status.HTTP_200_OK,
        )

   
