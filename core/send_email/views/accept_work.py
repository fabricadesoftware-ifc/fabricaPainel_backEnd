from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.fabrica_painel.models import Work


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def accept_work(request, work_id: int):
    try:
        work: Work = Work.objects.get(id=work_id)
    except Work.DoesNotExist:
        return Response(
            {"error": "Trabalho não encontrado."},
            status=status.HTTP_404_NOT_FOUND,
        )

    # Enforces that the one accepting the work submission is work advisor
    if request.user != work.advisor:
        return Response(
            {"error": "Você não tem permissão para aceitar esse trabalho."},
            status=status.HTTP_403_FORBIDDEN,
        )

    work.initial_submission_work_date = timezone.now()
    work.save()

    print(work)

    return Response(
        {"message": "Trabalho aceito."},
        status=status.HTTP_200_OK,
    )
