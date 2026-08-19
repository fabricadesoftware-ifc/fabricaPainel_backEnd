import logging

from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone

from django_project.permissions import IsAdvisor

from core.work.infra.work_django_app.models import Work
from core.__seedwork.domain.actions.acceptance_window import advisor_decision_windows, is_within_window
from core.work.domain.validations.validate_advisor_work_limit import count_advisor_accepted_works

logger = logging.getLogger("work_acceptance")


@api_view(["GET"])
@permission_classes([IsAdvisor])
def advisor_work_limit_status(request, verification_token) -> Response:
    """
    Situação do orientador na edição de um trabalho, para a tela de decisão.

    Só existe para que a interface consiga desabilitar o botão de aceitar e
    explicar o motivo antes do clique, em vez de deixar o professor tentar e
    receber o erro. Quem de fato impede o aceite é accept_advisor_work — este
    endpoint é apenas informativo e nunca altera nada.
    """
    try:
        work = Work.objects.select_related("edition", "advisor").get(
            verification_token=verification_token
        )
    except Work.DoesNotExist:
        return Response({"error": "Trabalho não encontrado."}, status=status.HTTP_404_NOT_FOUND)

    if work.advisor_id != request.user.id:
        return Response(
            {"error": "Você não é o orientador deste trabalho."},
            status=status.HTTP_403_FORBIDDEN,
        )

    edition = work.edition
    limit = edition.works_per_advisor_max or 0
    accepted_works = count_advisor_accepted_works(work.advisor, edition, current_work_id=work.id)
    limit_reached = bool(limit) and accepted_works >= limit

    return Response(
        {
            "limit": limit,
            "accepted_works": accepted_works,
            "remaining": max(limit - accepted_works, 0) if limit else None,
            "limit_reached": limit_reached,
            "within_decision_window": is_within_window(
                timezone.localdate(), advisor_decision_windows(edition)
            ),
        },
        status=status.HTTP_200_OK,
    )
