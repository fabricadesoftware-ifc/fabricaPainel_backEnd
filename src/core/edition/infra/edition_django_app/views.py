from rest_framework.viewsets import ModelViewSet
from drf_spectacular.utils import extend_schema
from datetime import datetime, timedelta
from rest_framework.response import Response

from core.edition.domain.tasks import create_remind_advisor_to_verify_invites_task, create_work_expiration_tasks
from core.edition.infra.edition_django_app.models import Edition
from core.edition.infra.edition_django_app.serializers import (
    EditionDetailSerializer,
    EditionWriteSerializer
)
from core.edition.infra.edition_django_app.filters import EditionFilter

from django_project.permissions import IsAdminOrManagementOrReadOnly

@extend_schema(tags=["edition"])
class EditionViewSet(ModelViewSet):
    queryset = Edition.objects.all()
    serializer_class = EditionDetailSerializer
    filterset_class = EditionFilter
    permission_classes = [IsAdminOrManagementOrReadOnly]

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return EditionDetailSerializer
        return EditionWriteSerializer
    http_method_names = ["get", "post", "patch", "delete"]
    
    def create(self, request, *args, **kwargs):
        try:
            create_remind_advisor_to_verify_invites_task(request)
            create_work_expiration_tasks(request)
        except Exception as e:
            return Response({"error": str(e)}, status=400)
        return super().create(request, *args, **kwargs)     
    
@extend_schema(tags=["edition"])
class EditionOpenViewSet(ModelViewSet):
    serializer_class = EditionDetailSerializer
    http_method_names = ["get"]

    def get_queryset(self):
        try:
            now = datetime.now()
            open_editions = Edition.objects.filter(
                initial_submission_date__lte=now,
                final_event_date__gte=now - timedelta(days=1)
            )
            if open_editions.exists():
                return open_editions
            # Sem edicao "aberta" no momento: retorna queryset vazio em vez de
            # None, que faria o DRF quebrar com erro 500 ao tentar filtrar/listar.
            return Edition.objects.none()
        except Exception as e:
            print("Erro no get_queryset da EditionOpenViewSet:", e)
            return Edition.objects.none()

