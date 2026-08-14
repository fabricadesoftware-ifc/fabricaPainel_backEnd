import logging

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

logger = logging.getLogger("work_acceptance")


@api_view(["GET"])
@throttle_classes([UserRateThrottle])
@permission_classes([IsAdvisor])
def accept_advisor_work(request, verification_token) -> Response:
    try:
        work = Work.objects.get(verification_token=verification_token)
    except Work.DoesNotExist:
        logger.warning(f"accept_advisor_work: token não encontrado ({verification_token})")
        return Response({"error": "Trabalho não encontrado."}, status=status.HTTP_404_NOT_FOUND)

    if work.status == 4:  # REJECTED
        logger.warning(f"accept_advisor_work: work {work.id} já rejeitado, aceite negado")
        return Response(
            {"error": "Este trabalho foi rejeitado e não pode mais ser aceito."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    edition = work.edition
    current_date = timezone.localdate()

    def within_acceptance_period() -> bool:
        return (
            edition.initial_advisor_acceptance <= current_date <= edition.final_advisor_acceptance
            or edition.initial_second_advisor_date <= current_date <= edition.final_second_advisor_date
        )

    if within_acceptance_period():
        work.advisor_status = WorkAdvisorStatusType.Type.APPROVED.value
        work.verification_token = uuid.uuid4()
        work._change_reason = "Orientador aceitou"
        work.save()

        students_ids = [s.id for s in work.team.team_members.all()]
        send_work_approve_email_to_student.delay(EMAIL_HOST_USER, students_ids, work.advisor.id)

        logger.info(
            f"accept_advisor_work: work {work.id} ('{work.title}') aceito por {work.advisor.email} "
            f"em {current_date}"
        )
        return Response({"message": "Orientação do trabalho aceita com sucesso."}, status=status.HTTP_200_OK)

    logger.warning(
        f"accept_advisor_work: work {work.id} ('{work.title}') NEGADO — fora do período de aceitação. "
        f"advisor={work.advisor.email} hoje={current_date} "
        f"1a_janela=[{edition.initial_advisor_acceptance}, {edition.final_advisor_acceptance}] "
        f"2a_janela=[{edition.initial_second_advisor_date}, {edition.final_second_advisor_date}]"
    )
    return Response(
        {"error": "O trabalho não está dentro do período de aceitação pelo orientador."},
        status=status.HTTP_400_BAD_REQUEST,
    )
