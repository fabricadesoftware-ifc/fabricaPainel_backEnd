from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from core.fabrica_painel.models import Work


@api_view(['GET'])
def accept_work(request, work_id: int):
    try:
        work: Work = Work.objects.get(id=work_id)
    except Work.DoesNotExist:
        return Response(
                {"error": "Trabalho não encontrado."},
                status=status.HTTP_404_NOT_FOUND,
            )

    work.initial_submission_work_date = timezone.now()
    work.save()

    print(work)

    return Response(
                {"message": "Trabalho aceito."},
                status=status.HTTP_404_NOT_FOUND,
            )
