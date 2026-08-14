import logging

from rest_framework.decorators import api_view, throttle_classes, permission_classes
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from rest_framework import status

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

    # Atualiza o status e limpa o token
    work_collaborator.status = WorkCollaboratorStatusType.Type.APPROVED.value
    work_collaborator.verification_token = None
    work_collaborator._change_reason = "Colaborador aceitou"
    work_collaborator.save()

    # Envia email para os estudantes
    students_ids = [s.id for s in work_collaborator.work.team.team_members.all()]
    send_collaborator_accept_email_to_student.delay(students_ids, work_collaborator.collaborator.id)

    logger.info(
        f"accept_collaborator_work: work {work_collaborator.work.id} ('{work_collaborator.work.title}') "
        f"colaboração aceita por {work_collaborator.collaborator.email}"
    )
    return Response(
        {"message": "Colaboração aceita com sucesso."},
        status=status.HTTP_200_OK,
    )
