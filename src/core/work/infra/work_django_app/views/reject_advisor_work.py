from rest_framework.decorators import api_view, throttle_classes, permission_classes, authentication_classes
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.utils import timezone

from core.work.infra.work_django_app.models import Work, WorkAdvisorStatusType
from django_project.settings import EMAIL_HOST_USER
from core.work.domain.tasks.send_email_student.reject.send_work_reject_advisor_email_to_student import send_work_reject_advisor_email_to_student

@throttle_classes([UserRateThrottle])
@api_view(["GET"])
@permission_classes([AllowAny])
@authentication_classes([])
def reject_advisor_work(request, verification_token) -> Response:
    try:
        work = Work.objects.get(verification_token=verification_token)
    except Work.DoesNotExist:
        return Response(
            {"error": "Trabalho não encontrado."},
            status=status.HTTP_404_NOT_FOUND,
        )

    # Validação adicional: garantir que o advisor é professor
    if work.advisor.user_type != work.advisor.TEACHER:
        return Response(
            {"error": "Apenas professores podem ser orientadores."},
            status=status.HTTP_403_FORBIDDEN,
        )

    # Pega os IDs dos estudantes
    students_ids = [s.id for s in work.team.team_members.all()]
    from_email = EMAIL_HOST_USER

    # Atualiza o status do orientador para CANCELED
    work.advisor_status = WorkAdvisorStatusType.Type.CANCELED.value
    work.verification_token = None
    work.save()

    # Envia email para os estudantes
    send_work_reject_advisor_email_to_student.delay(from_email, students_ids)

    return Response(
        {"message": "Orientação do trabalho rejeitada com sucesso."},
        status=status.HTTP_200_OK,
    ) 