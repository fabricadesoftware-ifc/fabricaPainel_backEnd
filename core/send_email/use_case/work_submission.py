from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from core.fabrica_painel.models import Work

"""
Create an use case so that the
    advisor receives an e-mail with all of the work info
        when a student submits the work.

If the work is accepted by the advisor,
    initial_submission_work_date will be filled,
otherwise,
    the submission will be rejected.
"""


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def send_email_to_advisor(request):
    work_id: int = request.data.get("work_id")
    advisor_email: str = request.data.get("advisor_email")

    if not work_id:
        return Response(
            {"message": _("No work ID provided.")}, status=status.HTTP_400_BAD_REQUEST
        )

    if not advisor_email:
        return Response(
            {"message": _("Empty e-mail.")}, status=status.HTTP_400_BAD_REQUEST
        )

    work = Work.objects.get(id=work_id)
    work.initial_submission_work_date = timezone.now()
    work.save()

    return Response(
        {"message": _("E-mail successfully sent")}, status=status.HTTP_200_OK
    )
