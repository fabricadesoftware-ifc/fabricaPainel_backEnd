import logging

from django.utils import timezone
from rest_framework.decorators import api_view, throttle_classes, permission_classes
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from rest_framework import status

from core.__seedwork.domain.actions.acceptance_window import advisor_decision_windows, is_within_window
from core.work.infra.work_django_app.models import WorkCollaborator, WorkCollaboratorStatusType
from core.user.infra.user_django_app.models import User
from django_project.permissions import IsCollaborator
from core.work.domain.tasks.send_email_student.send_collaborator_response_email_to_student import (
    send_collaborator_accept_email_to_student,
)

logger = logging.getLogger("work_acceptance")


@api_view(["GET"])
@throttle_classes([UserRateThrottle])
@permission_classes([IsCollaborator])
def accept_collaborator_work(request, verification_token) -> Response:
    try:
        work_collaborator = WorkCollaborator.objects.get(verification_token=verification_token)
    except WorkCollaborator.DoesNotExist:
        logger.warning(f"accept_collaborator_work: token não encontrado ({verification_token})")
        return Response(
            {"error": "Convite de colaboração não encontrado."},
            status=status.HTTP_404_NOT_FOUND,
        )

    if work_collaborator.work.status == 4:  # REJECTED
        logger.warning(
            f"accept_collaborator_work: work {work_collaborator.work.id} já rejeitado, aceite negado "
            f"(colaborador {work_collaborator.collaborator.email})"
        )
        return Response(
            {"error": "Este trabalho foi rejeitado e não pode mais ser aceito."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    windows = advisor_decision_windows(work_collaborator.work.edition)
    if not is_within_window(timezone.localdate(), windows):
        return Response(
            {"error": "O período para aceitar esta colaboração já foi encerrado."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Atualiza o status e limpa o token
    work_collaborator.status = WorkCollaboratorStatusType.Type.APPROVED.value
    work_collaborator.verification_token = None
    work_collaborator._change_reason = "Colaborador aceitou"
    work_collaborator.save()

    # Envia email para os estudantes
    students_ids = [s.id for s in work_collaborator.work.team.team_members.all()]
    # Mesma proteção do aceite de orientação: a aceitação já foi gravada e o token já
    # foi limpo, então uma falha no broker não pode virar 500 pro colaborador.
    try:
        send_collaborator_accept_email_to_student.delay(students_ids, work_collaborator.collaborator.id)
    except Exception as exc:
        logger.error(
            f"accept_collaborator_work: work {work_collaborator.work.id} com colaboração aceita, "
            f"mas falhou ao enfileirar o email de aviso aos alunos: {exc}"
        )

    logger.info(
        f"accept_collaborator_work: work {work_collaborator.work.id} ('{work_collaborator.work.title}') "
        f"colaboração aceita por {work_collaborator.collaborator.email}"
    )
    return Response(
        {"message": "Colaboração aceita com sucesso."},
        status=status.HTTP_200_OK,
    )
