from rest_framework.decorators import api_view, throttle_classes, permission_classes
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.utils import timezone

from core.work.infra.work_django_app.models import Work, WorkStatusType
from django_project.settings import EMAIL_HOST_USER
from django_project.permissions import IsAdvisor
from core.work.domain.tasks.send_email_student.approve.send_work_approve_email_to_student import send_work_approve_email_to_student
from core.work.domain.tasks.send_email_student.needs_changes.send_work_needs_changes_email_to_student import send_work_needs_changes_email_to_student

@api_view(["GET"])
@throttle_classes([UserRateThrottle])
@permission_classes([IsAdvisor])
def accept_submission(request, verification_token) -> Response:
    try:
        work = Work.objects.get(verification_token=verification_token)
    except Work.DoesNotExist:
        return Response(
            {"error": "Trabalho não encontrado."},
            status=status.HTTP_404_NOT_FOUND,
        )

    # Pega os IDs dos estudantes
    students_ids = [s.id for s in work.team.team_members.all()]
    from_email = EMAIL_HOST_USER
    advisor_id = work.advisor.id

    # Atualiza o status do trabalho para APPROVED
    work.status = WorkStatusType.Type.APPROVED.value
    work.verification_token = None
    work._change_reason = "Trabalho aprovado"
    work.save()

    # Envia email para os estudantes
    send_work_approve_email_to_student.delay(from_email, students_ids, advisor_id)

    return Response(
        {"message": "Trabalho aprovado com sucesso."},
        status=status.HTTP_200_OK,
    )

@api_view(["GET"])
@throttle_classes([UserRateThrottle])
@permission_classes([IsAdvisor])
def reject_submission(request, verification_token) -> Response:
    try:
        work = Work.objects.get(verification_token=verification_token)
    except Work.DoesNotExist:
        return Response(
            {"error": "Trabalho não encontrado."},
            status=status.HTTP_404_NOT_FOUND,
        )

    # Pega os IDs dos estudantes
    students_ids = [s.id for s in work.team.team_members.all()]
    message = request.query_params.get("message", "")
    
    # Atualiza o status do trabalho para NEEDS_CHANGES
    work.status = WorkStatusType.Type.NEEDS_CHANGES.value
    work.verification_token = None
    work.needs_changes_submission_work_date = timezone.now()
    work._change_reason = "Solicitado ajuste"
    work.save()

    # Envia email para os estudantes
    send_work_needs_changes_email_to_student.delay(students_ids, message, work.title)

    return Response(
        {"message": "Trabalho rejeitado com sucesso. Os alunos serão notificados para fazer as alterações necessárias."},
        status=status.HTTP_200_OK,
    ) 
