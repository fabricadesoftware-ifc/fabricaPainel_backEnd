import os 
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from dotenv import load_dotenv

from core.fabrica_painel.tasks.send_email_student import send_work_approve_email_to_student
from core.fabrica_painel.tasks.send_email_student import send_work_new_status_approve_email_to_student
from core.fabrica_painel.models import Edition
from core.fabrica_painel.models import Work


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
    student = work.team.team_student
    student_id = student.id

    from_email = os.getenv("EMAIL_HOST_USER")
    edition = Edition.objects.get(id=work.edition.id)

    if work.status == Work.WorkStatus.REJECTED and edition.final_advisor_date > timezone.now():
        print(edition.final_advisor_date)
        work.final_submission_work_date = timezone.now()
        work.verification_token = None
        work.status = Work.WorkStatus.APPROVED
        work.reject_submission_work_date = None
        work.save()

        if work.final_submission_work_date is not None:
            send_work_new_status_approve_email_to_student.delay(from_email, student_id)
            return Response(
        {"message": "O trabalho que tinha sido recusado foi aceito."},
        status=status.HTTP_200_OK,
        )

    elif edition.final_advisor_date > timezone.now():
        print(edition.final_advisor_date, "adsad")
        work.final_submission_work_date = timezone.now()
        work.verification_token = None
        work.status = Work.WorkStatus.APPROVED
        work.save()

        if work.final_submission_work_date is not None:
            send_work_approve_email_to_student.delay(from_email, student_id)
        return Response(
        {"message": "Trabalho aceito."},
        status=status.HTTP_200_OK,
        )

    return Response(
        {"error": "Data limite para aceitar o trabalho expirou."},
        )
   
