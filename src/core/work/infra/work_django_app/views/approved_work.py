from rest_framework.decorators import api_view, throttle_classes, permission_classes
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from rest_framework import status
from django.utils import timezone

from django_project.settings import EMAIL_HOST_USER
from django_project.permissions import IsAdvisor
from core.work.infra.work_django_app.models import Work, WorkStatusType, Edition
from core.work.domain.tasks import send_work_approve_email_to_student, send_work_new_status_approve_email_to_student


@api_view(["GET"])
@throttle_classes([UserRateThrottle])
@permission_classes([IsAdvisor])
def approve_work(request, verification_token) -> Response:
    try:
        work = Work.objects.get(verification_token=verification_token)
    except Work.DoesNotExist:
        return Response({"error": "Trabalho não encontrado."}, status=status.HTTP_404_NOT_FOUND)

    students_ids = list(work.team.team_members.values_list("id", flat=True))
    edition = work.edition
    current_date = timezone.localdate()
    from_email = EMAIL_HOST_USER

    def within_submission_period() -> bool:
        return (
            edition.initial_submission_date <= current_date <= edition.final_advisor_acceptance
            or edition.initial_second_submission_date <= current_date <= edition.final_second_advisor_date
        )

    if not within_submission_period():
        return Response({"error": "Fora do período de submissão."}, status=status.HTTP_401_UNAUTHORIZED)

    # Aprova o trabalho
    work.status = WorkStatusType.Type.APPROVED.value
    work.verification_token = None
    work.save()

    # Envia email de status aprovado se houver final_submission_date definido
    if edition.final_submission_date:
        send_work_new_status_approve_email_to_student.delay(from_email, students_ids)

    return Response({"message": "Trabalho aprovado com sucesso."}, status=status.HTTP_200_OK)
