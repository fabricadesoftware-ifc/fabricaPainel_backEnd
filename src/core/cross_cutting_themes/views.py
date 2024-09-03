from rest_framework import viewsets
from drf_spectacular.utils import extend_schema

from core.cross_cutting_themes.models import CrossCuttingTheme
from core.cross_cutting_themes.serializers import CrossCuttingThemeSerializer


@extend_schema(tags=["cross_cutting_themes"])
class CrossCuttingThemeViewSet(viewsets.ModelViewSet):
    queryset = CrossCuttingTheme.objects.all()
    serializer_class = CrossCuttingThemeSerializer
    http_method_names: list[str] = ["get", "post", "put", "delete"]
