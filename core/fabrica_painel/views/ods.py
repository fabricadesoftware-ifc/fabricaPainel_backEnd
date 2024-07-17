from rest_framework.viewsets import ModelViewSet
from drf_spectacular.utils import extend_schema
from core.fabrica_painel.models.ods import SustainableGoals
from core.fabrica_painel.serializers.ods import SustainableGoalsSerializer  


@extend_schema(tags=["ods"])
class SustainableGoalsViewSet(ModelViewSet):
    queryset = SustainableGoals.objects.all()
    serializer_class = SustainableGoalsSerializer
    http_method_names = ["get", "post", "patch", "delete"]