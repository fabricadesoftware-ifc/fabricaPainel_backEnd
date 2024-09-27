from rest_framework.decorators import api_view, throttle_classes
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from rest_framework import status
from django.utils import timezone

from django_project.settings import EMAIL_HOST_USER
from core.work.domain.tasks import send_work_approve_email_to_student
from core.work.domain.tasks import send_work_new_status_approve_email_to_student
from core.work.infra.work_django_app.models import Edition
from core.work.infra.work_django_app.models import Work

@throttle_classes([UserRateThrottle])
@api_view(["GET"])
def approve_work(request, verification_token) -> Response:
    try:
        work = Work.objects.get(verification_token=verification_token)
    except Work.DoesNotExist:
        return Response(
            {"error": "Trabalho não encontrado."},
            status=status.HTTP_404_NOT_FOUND,
        )
    student = work.team.team_members
    students_ids = []
    for s in student.all():
        students_ids.append(s.id)
    

    from_email = EMAIL_HOST_USER
    edition = Edition.objects.get(id=work.edition.id)

    if work.status == Work.WorkStatus.REJECTED and edition.final_advisor_date > timezone.now():
        print(edition.final_advisor_date)
        work.final_submission_work_date = timezone.now()
        work.verification_token = None
        work.status = Work.WorkStatus.APPROVED
        work.reject_submission_work_date = None
        work.save()


        if work.final_submission_work_date is not None:
            send_work_new_status_approve_email_to_student.delay(from_email, students_ids)
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
            send_work_approve_email_to_student.delay(from_email, students_ids)
        return Response(
        {"message": "Trabalho aceito."},
        status=status.HTTP_200_OK,
        )

    return Response(
        {"error": "Data limite para aceitar o trabalho expirou."},
        )
   
