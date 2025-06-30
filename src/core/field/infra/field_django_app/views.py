from rest_framework.viewsets import ModelViewSet
from drf_spectacular.utils import extend_schema

from core.field.infra.field_django_app.models import Field
from core.field.infra.field_django_app.serializers import FieldRetriveSerializer, FieldWriteSerializer
from core.field.infra.field_django_app.filters import FieldFilter   

from django_project.permissions import IsAdminOrReadOnly

@extend_schema(tags=["field"])
class FieldViewSet(ModelViewSet):
    queryset = Field.objects.all()
    serializer_class = FieldRetriveSerializer
    filterset_class = FieldFilter
    permission_classes = [IsAdminOrReadOnly]

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return FieldRetriveSerializer
        return FieldWriteSerializer
    http_method_names = ["get", "post", "patch", "delete"]



