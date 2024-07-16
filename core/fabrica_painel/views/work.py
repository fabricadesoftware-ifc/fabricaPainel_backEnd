from rest_framework.viewsets import ModelViewSet
from drf_spectacular.utils import extend_schema
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.permissions import AllowAny


from core.fabrica_painel.models.work import Work
from core.fabrica_painel.serializers.work import (
    WorkDetailSerializer,
    WorkWriteSerializer
)


@extend_schema(tags=["work"])
class WorkViewSet(ModelViewSet):
    queryset = Work.objects.all()
    serializer_class = WorkDetailSerializer

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return WorkDetailSerializer
        return WorkWriteSerializer
    http_method_names = ["get", "post", "patch", "delete"]


@api_view(["GET"])
def accept_work(request, verification_token) -> Response:
    try:
        work: Work = Work.objects.get(verification_token=verification_token)

    except Work.DoesNotExist:
        return Response(
            {"error": "Trabalho não encontrado."},
            status=status.HTTP_404_NOT_FOUND,
        )

    work.final_submission_work_date = timezone.now()
    work.verification_token = None
    work.save()

    return Response(
        {"message": "Trabalho aceito."},
        status=status.HTTP_200_OK,
    )
