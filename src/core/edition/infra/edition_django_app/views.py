from rest_framework.viewsets import ModelViewSet
from drf_spectacular.utils import extend_schema

from core.edition.infra.edition_django_app.models import Edition
from core.edition.infra.edition_django_app.serializers import (
    EditionDetailSerializer,
    EditionWriteSerializer
)

@extend_schema(tags=["edition"])
class EditionViewSet(ModelViewSet):
    queryset = Edition.objects.all()
    serializer_class = EditionDetailSerializer

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return EditionDetailSerializer
        return EditionWriteSerializer
    http_method_names = ["get", "post", "patch", "delete"]
    