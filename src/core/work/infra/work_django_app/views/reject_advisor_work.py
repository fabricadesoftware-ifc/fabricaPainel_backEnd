import logging

from rest_framework.decorators import api_view, throttle_classes, permission_classes
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from rest_framework import status
from django.utils import timezone
import uuid

from core.work.infra.work_django_app.models import Work, WorkAdvisorStatusType
from django_project.settings import EMAIL_HOST_USER
from django_project.permissions import IsAdvisor
from core.work.domain.tasks.send_email_student.reject.send_work_reject_advisor_email_to_student import (
    send_work_reject_advisor_email_to_student,
)

logger = logging.getLogger("work_acceptance")


@api_view(["GET"])
@throttle_classes([UserRateThrottle])
@permission_classes([IsAdvisor])
def reject_advisor_work(request, verification_token) -> Response:
    try:
        work = Work.objects.get(verification_token=verification_token)
    except Work.DoesNotExist:
        logger.warning(f"reject_advisor_work: token não encontrado ({verification_token})")
        return Response({"error": "Trabalho não encontrado."}, status=status.HTTP_404_NOT_FOUND)

    if work.status == 4:  # REJECTED
        logger.warning(f"reject_advisor_work: work {work.id} já estava rejeitado")
        return Response(
            {"error": "Este trabalho já foi rejeitad"},
            status=status.HTTP_204_NO_CONTENT,
        )

    # Atualiza o status do orientador e gera novo token
    work.advisor_status = WorkAdvisorStatusType.Type.REJECTED.value
    work.verification_token = uuid.uuid4()
    work._change_reason = "Orientador recusou"
    work.save()

    students_ids = list(work.team.team_members.values_list("id", flat=True))
    send_work_reject_advisor_email_to_student.delay(EMAIL_HOST_USER, students_ids)

    logger.info(
        f"reject_advisor_work: work {work.id} ('{work.title}') recusado por {work.advisor.email} "
        f"em {timezone.localdate()}"
    )
    return Response({"message": "Orientação do trabalho rejeitada com sucesso."}, status=status.HTTP_200_OK)
