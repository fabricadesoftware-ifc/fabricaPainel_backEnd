from rest_framework.decorators import api_view, throttle_classes, permission_classes, authentication_classes
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.utils import timezone

from core.work.infra.work_django_app.models import Work, WorkCollaborator, WorkCollaboratorStatusType
from django_project.settings import EMAIL_HOST_USER
from core.user.infra.user_django_app.models import User
from core.work.domain.tasks.send_email_student.send_collaborator_response_email_to_student import send_collaborator_accept_email_to_student

@throttle_classes([UserRateThrottle])
@api_view(["GET"])
@permission_classes([AllowAny])
@authentication_classes([])
def accept_collaborator_work(request, verification_token) -> Response:
    try:
        work = Work.objects.get(verification_token=verification_token)
    except Work.DoesNotExist:
        return Response(
            {"error": "Trabalho não encontrado."},
            status=status.HTTP_404_NOT_FOUND,
        )

    # Pega o email do colaborador a partir dos parâmetros da query
    collaborator_email = request.query_params.get('collaborator_email')
    if not collaborator_email:
        return Response(
            {"error": "Email do colaborador não fornecido."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        collaborator = User.objects.get(email=collaborator_email, is_collaborator=True)
    except User.DoesNotExist:
        return Response(
            {"error": "Colaborador não encontrado."},
            status=status.HTTP_404_NOT_FOUND,
        )

    # Verifica se já existe uma relação para este colaborador com este trabalho
    try:
        work_collaborator = WorkCollaborator.objects.get(work=work, collaborator=collaborator)
        work_collaborator.status = WorkCollaboratorStatusType.Type.APPROVED.value
        work_collaborator.save()
    except WorkCollaborator.DoesNotExist:
        return Response(
            {"error": "Convite de colaboração não encontrado."},
            status=status.HTTP_404_NOT_FOUND,
        )

    # Limpa o token de verificação
    work.verification_token = None
    work.save()

    # Envia email para os estudantes informando que o colaborador aceitou
    students_ids = [s.id for s in work.team.team_members.all()]
    send_collaborator_accept_email_to_student.delay(students_ids, collaborator.id)

    return Response(
        {"message": "Colaboração aceita com sucesso."},
        status=status.HTTP_200_OK,
    ) 