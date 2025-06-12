from rest_framework.viewsets import ModelViewSet
from drf_spectacular.utils import extend_schema
from datetime import datetime, timedelta
from rest_framework.response import Response

from core.edition.domain.tasks.advisors_periodic_task import create_remind_advisor_to_verify_invites_task
from core.edition.infra.edition_django_app.models import Edition
from core.edition.infra.edition_django_app.serializers import (
    EditionDetailSerializer,
    EditionWriteSerializer
)
from core.edition.infra.edition_django_app.filters import EditionFilter

from django_project.permissions import IsAdminOrReadOnly

@extend_schema(tags=["edition"])
class EditionViewSet(ModelViewSet):
    queryset = Edition.objects.all()
    serializer_class = EditionDetailSerializer
    filterset_class = EditionFilter
    permission_classes = [IsAdminOrReadOnly]

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return EditionDetailSerializer
        return EditionWriteSerializer
    http_method_names = ["get", "post", "patch", "delete"]
    
    def create(self, request, *args, **kwargs):
        try:
            create_remind_advisor_to_verify_invites_task(request)
        except Exception as e:
            return Response({"error": str(e)}, status=400)
        return super().create(request, *args, **kwargs)     
    
@extend_schema(tags=["edition"])
class EditionOpenViewSet(ModelViewSet):
    serializer_class = EditionDetailSerializer
    http_method_names = ["get"]

    def get_queryset(self):
        now = datetime.now()
        return Edition.objects.filter(
            initial_submission_date__lte=now,
            final_event_date__gte=now - timedelta(days=1)
        )

