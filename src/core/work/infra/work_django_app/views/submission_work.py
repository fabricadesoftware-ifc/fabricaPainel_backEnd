import logging

from rest_framework.decorators import api_view, throttle_classes, permission_classes
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.utils import timezone

from core.work.infra.work_django_app.models import Work, WorkStatusType, WorkAdvisorStatusType
from django_project.settings import EMAIL_HOST_USER
from django_project.permissions import IsAdvisor
from core.work.domain.tasks.send_email_student.approve.send_work_approve_email_to_student import send_work_approve_email_to_student
from core.work.domain.tasks.send_email_student.needs_changes.send_work_needs_changes_email_to_student import send_work_needs_changes_email_to_student
from core.__seedwork.domain.actions.acceptance_window import advisor_decision_windows, is_within_window

logger = logging.getLogger("work_acceptance")

@api_view(["GET"])
@throttle_classes([UserRateThrottle])
@permission_classes([IsAdvisor])
def accept_submission(request, verification_token) -> Response:
    try:
        work = Work.objects.get(verification_token=verification_token)
    except Work.DoesNotExist:
        logger.warning(f"accept_submission: token não encontrado ({verification_token})")
        return Response(
            {"error": "Trabalho não encontrado."},
            status=status.HTTP_404_NOT_FOUND,
        )

    if work.advisor_id != request.user.id:
        logger.warning(
            f"accept_submission: usuario {request.user.id} tentou decidir o work {work.id} sem ser o orientador dele"
        )
        return Response(
            {"error": "Apenas o orientador deste trabalho pode tomar esta decisão."},
            status=status.HTTP_403_FORBIDDEN,
        )

    # Idempotente: a aprovação agora acontece junto do aceite da orientação, e o
    # front antigo ainda chama este endpoint em seguida.
    if work.status == WorkStatusType.Type.APPROVED.value:
        return Response(
            {"message": "Trabalho aprovado com sucesso."},
            status=status.HTTP_200_OK,
        )

    if work.advisor_status != WorkAdvisorStatusType.Type.APPROVED.value:
        logger.warning(
            f"accept_submission: work {work.id} ('{work.title}') NEGADO — orientador ainda não aceitou orientar"
        )
        return Response(
            {"error": "O orientador ainda não aceitou orientar este trabalho."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    edition = work.edition
    current_date = timezone.localdate()
    # Mesma janela usada em accept_advisor_work: aprovar o trabalho é uma decisão do
    # orientador, então segue o prazo dele, e não o prazo de envio dos alunos.
    windows = advisor_decision_windows(edition)

    if not is_within_window(current_date, windows):
        logger.warning(
            f"accept_submission: work {work.id} ('{work.title}') NEGADO — fora do período de decisão do orientador. "
            f"hoje={current_date} 1a_janela=[{edition.initial_advisor_acceptance}, {edition.final_advisor_acceptance}] "
            f"2a_janela=[{edition.initial_second_advisor_date}, {edition.final_second_advisor_date}]"
        )
        return Response(
            {"error": "O trabalho não está dentro do período de aprovação pelo orientador."},
            status=status.HTTP_400_BAD_REQUEST,
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

    logger.info(
        f"accept_submission: work {work.id} ('{work.title}') aprovado por {work.advisor.email} "
        f"em {timezone.localdate()}"
    )
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
        logger.warning(f"reject_submission: token não encontrado ({verification_token})")
        return Response(
            {"error": "Trabalho não encontrado."},
            status=status.HTTP_404_NOT_FOUND,
        )

    if work.advisor_id != request.user.id:
        logger.warning(
            f"reject_submission: usuario {request.user.id} tentou decidir o work {work.id} sem ser o orientador dele"
        )
        return Response(
            {"error": "Apenas o orientador deste trabalho pode tomar esta decisão."},
            status=status.HTTP_403_FORBIDDEN,
        )

    # Mesmas travas do aceite: orientação aprovada, dentro do prazo do orientador,
    # e só a partir de um trabalho ainda em análise (pendente ou com ajustes).
    if work.advisor_status != WorkAdvisorStatusType.Type.APPROVED.value:
        return Response(
            {"error": "O orientador ainda não aceitou orientar este trabalho."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if work.status not in (WorkStatusType.Type.PENDING.value, WorkStatusType.Type.NEEDS_CHANGES.value):
        return Response(
            {"error": "Este trabalho não está mais em análise."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if not is_within_window(timezone.localdate(), advisor_decision_windows(work.edition)):
        return Response(
            {"error": "O trabalho não está dentro do período de aprovação pelo orientador."},
            status=status.HTTP_400_BAD_REQUEST,
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

    logger.info(
        f"reject_submission: work {work.id} ('{work.title}') marcado como precisa-de-ajustes por "
        f"{work.advisor.email} em {timezone.localdate()} — mensagem: {message!r}"
    )
    return Response(
        {"message": "Trabalho rejeitado com sucesso. Os alunos serão notificados para fazer as alterações necessárias."},
        status=status.HTTP_200_OK,
    )
