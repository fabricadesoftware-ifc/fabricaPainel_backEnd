from rest_framework.decorators import api_view, throttle_classes, permission_classes, authentication_classes
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.utils import timezone

from core.work.infra.work_django_app.models import Work, WorkCollaborator, WorkCollaboratorStatusType
from django_project.settings import EMAIL_HOST_USER
from core.user.infra.user_django_app.models import User
from core.work.domain.tasks.send_email_student.send_collaborator_response_email_to_student import send_collaborator_reject_email_to_student

@throttle_classes([UserRateThrottle])
@api_view(["GET"])
@permission_classes([AllowAny])
@authentication_classes([])
def reject_collaborator_work(request, verification_token) -> Response:
    try:
        work_collaborator = WorkCollaborator.objects.get(verification_token=verification_token)
    except WorkCollaborator.DoesNotExist:
        return Response(
            {"error": "Convite de colaboração não encontrado."},
            status=status.HTTP_404_NOT_FOUND,
        )

    # Verifica se o trabalho não está rejeitado
    if work_collaborator.work.status == 4:  # REJECTED
        return Response(
            {"error": "Este trabalho foi rejeitado e não pode mais ser aceito."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Validação adicional: garantir que o colaborador não é estudante
    if work_collaborator.collaborator.user_type == User.STUDENT:
        return Response(
            {"error": "Estudantes não podem ser colaboradores."},
            status=status.HTTP_403_FORBIDDEN,
        )

    # Atualiza o status para CANCELED
    work_collaborator.status = WorkCollaboratorStatusType.Type.CANCELED.value
    work_collaborator.verification_token = None  # Limpa o token
    work_collaborator.save()

    # Envia email para os estudantes informando que o colaborador rejeitou
    students_ids = [s.id for s in work_collaborator.work.team.team_members.all()]
    send_collaborator_reject_email_to_student.delay(students_ids, work_collaborator.collaborator.id)

    return Response(
        {"message": "Colaboração rejeitada com sucesso."},
        status=status.HTTP_200_OK,
    ) 