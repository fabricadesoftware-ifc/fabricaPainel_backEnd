import logging

from rest_framework.decorators import api_view, throttle_classes, permission_classes
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from rest_framework import status
from django.utils import timezone
from django_project.permissions import IsAdvisor

from core.work.infra.work_django_app.models import Work, WorkAdvisorStatusType, Edition
# Import sem uso direto: mantido porque test_edition_flow.py patcha este caminho.
from core.work.domain.tasks.send_email_student.approve.send_work_approve_email_to_student import (
    send_work_approve_email_to_student,
)
from core.__seedwork.domain.actions.acceptance_window import advisor_decision_windows, is_within_window
from core.work.domain.validations.validate_advisor_work_limit import count_advisor_accepted_works
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
    windows = advisor_decision_windows(edition)

    # O limite de orientações só era conferido no front, na hora de escolher o
    # orientador, e contando apenas os aceites já confirmados. Enquanto o professor
    # não respondia nada ele aparecia com todas as vagas livres, então várias equipes
    # conseguiam convidá-lo e ele aceitava todas. A vaga é ocupada aqui, no aceite,
    # e é aqui que o limite precisa valer.
    limit = edition.works_per_advisor_max
    if limit:
        accepted_works = count_advisor_accepted_works(work.advisor, edition, current_work_id=work.id)
        if accepted_works >= limit:
            logger.warning(
                f"accept_advisor_work: work {work.id} ('{work.title}') NEGADO — limite de orientações "
                f"atingido. advisor={work.advisor.email} aceitos={accepted_works} limite={limit} "
                f"edicao={edition.id}"
            )
            return Response(
                {
                    "error": (
                        f"Você já atingiu o limite de {limit} trabalho(s) orientados nesta edição "
                        f"e não pode aceitar esta orientação."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

    if is_within_window(current_date, windows):
        work.advisor_status = WorkAdvisorStatusType.Type.APPROVED.value
        work.verification_token = uuid.uuid4()
        work._change_reason = "Orientador aceitou"
        work.save()

        # Email de aprovação é enviado em /accept-submission/, não aqui, pra não duplicar.
        logger.info(
            f"accept_advisor_work: work {work.id} ('{work.title}') aceito por {work.advisor.email} "
            f"em {current_date}"
        )
        # Token novo devolvido pro caller poder chamar /accept-submission/ em seguida.
        return Response(
            {
                "message": "Orientação do trabalho aceita com sucesso.",
                "work_id": str(work.id),
                "verification_token": str(work.verification_token),
            },
            status=status.HTTP_200_OK,
        )

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
