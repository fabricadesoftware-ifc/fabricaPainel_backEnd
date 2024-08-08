from rest_framework.viewsets import ModelViewSet
from drf_spectacular.utils import extend_schema
from core.fabrica_painel.models.ods import Ods
from core.fabrica_painel.serializers.ods import OdsSerializer  


@extend_schema(tags=["ods"])
class OdsViewSet(ModelViewSet):
    queryset = Ods.objects.all()
    serializer_class = OdsSerializer
    http_method_names = ["get", "post", "patch", "delete"]