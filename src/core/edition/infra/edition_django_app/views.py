from rest_framework.viewsets import ModelViewSet
from drf_spectacular.utils import extend_schema
from datetime import datetime, timedelta

from core.edition.infra.edition_django_app.models import Edition
from core.edition.infra.edition_django_app.serializers import (
    EditionDetailSerializer,
    EditionWriteSerializer
)
from core.edition.infra.edition_django_app.filters import EditionFilter

@extend_schema(tags=["edition"])
class EditionViewSet(ModelViewSet):
    queryset = Edition.objects.all()
    serializer_class = EditionDetailSerializer
    filterset_class = EditionFilter

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return EditionDetailSerializer
        return EditionWriteSerializer
    http_method_names = ["get", "post", "patch", "delete"]
    
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

