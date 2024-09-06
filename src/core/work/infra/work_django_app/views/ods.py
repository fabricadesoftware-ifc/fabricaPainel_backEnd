from rest_framework.viewsets import ModelViewSet
from drf_spectacular.utils import extend_schema
from core.work.infra.work_django_app.models import Ods
from core.work.infra.work_django_app.serializers import OdsSerializer

@extend_schema(tags=["ods"])
class OdsViewSet(ModelViewSet):
    queryset = Ods.objects.all()
    serializer_class = OdsSerializer
    http_method_names = ["get", "post", "patch", "delete"]


