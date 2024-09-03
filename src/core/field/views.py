from rest_framework.viewsets import ModelViewSet
from drf_spectacular.utils import extend_schema

from core.field.models import Field
from core.field.serializers import FieldRetriveSerializer, FieldWriteSerializer

@extend_schema(tags=["field"])
class FieldViewSet(ModelViewSet):
    queryset = Field.objects.all()
    serializer_class = FieldRetriveSerializer

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return FieldRetriveSerializer
        return FieldWriteSerializer
    http_method_names = ["get", "post", "patch", "delete"]



