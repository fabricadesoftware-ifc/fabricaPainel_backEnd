from drf_spectacular.utils import extend_schema
from rest_framework.viewsets import ModelViewSet
from rest_framework.throttling import UserRateThrottle
 
from core.work.infra.work_django_app.models import Ods
from core.work.infra.work_django_app.serializers import OdsSerializer
from core.work.infra.work_django_app.filters import OdsFilter

from django_project.permissions import IsAdminOrReadOnly

@extend_schema(tags=["ods"])
class OdsViewSet(ModelViewSet):
    queryset = Ods.objects.all()
    serializer_class = OdsSerializer
    throttle_classes = [UserRateThrottle]
    http_method_names = ["get", "post", "patch", "delete"]
    filterset_class = OdsFilter
    permission_classes = [IsAdminOrReadOnly]


