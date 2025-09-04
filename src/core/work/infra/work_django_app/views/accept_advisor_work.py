from rest_framework.decorators import api_view, throttle_classes, permission_classes
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from rest_framework import status
from django.utils import timezone
from django_project.settings import EMAIL_HOST_USER
from django_project.permissions import IsAdvisor

from core.work.infra.work_django_app.models import Work, WorkAdvisorStatusType, Edition
from core.work.domain.tasks.send_email_student.approve.send_work_approve_email_to_student import (
    send_work_approve_email_to_student,
)
import uuid


@throttle_classes([UserRateThrottle])
@api_view(["GET"])
@permission_classes([IsAdvisor])
def accept_advisor_work(request, verification_token) -> Response:
    try:
        work = Work.objects.get(verification_token=verification_token)
    except Work.DoesNotExist:
        return Response({"error": "Trabalho não encontrado."}, status=status.HTTP_404_NOT_FOUND)

    if work.status == 4:  # REJECTED
        return Response(
            {"error": "Este trabalho foi rejeitado e não pode mais ser aceito."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    edition = work.edition
    current_date = timezone.now().date()

    def within_acceptance_period() -> bool:
        return (
            edition.initial_submission_date <= current_date <= edition.final_advisor_acceptance
            or edition.initial_second_submission_date <= current_date <= edition.final_second_advisor_date
        )

    if within_acceptance_period():
        work.advisor_status = WorkAdvisorStatusType.Type.APPROVED.value
        work.verification_token = uuid.uuid4()
        work.save()

        students_ids = [s.id for s in work.team.team_members.all()]
        send_work_approve_email_to_student.delay(EMAIL_HOST_USER, students_ids, work.advisor.id)

        return Response({"message": "Orientação do trabalho aceita com sucesso."}, status=status.HTTP_200_OK)

    return Response(
        {"error": "O trabalho não está dentro do período de aceitação pelo orientador."},
        status=status.HTTP_400_BAD_REQUEST,
    )
