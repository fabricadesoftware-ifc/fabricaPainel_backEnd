from rest_framework.viewsets import ModelViewSet
from drf_spectacular.utils import extend_schema
from rest_framework.throttling import UserRateThrottle
from django_project.permissions import IsAuthenticatedReadAdminManagementWrite

from core.work.infra.work_django_app.models import Keyword
from core.work.infra.work_django_app.serializers import KeywordDetailSerializer, KeywordWriteSerializer

@extend_schema(tags=["keyword"])
class KeywordViewSet(ModelViewSet):
    queryset = Keyword.objects.all()
    serializer_class = KeywordDetailSerializer
    throttle_classes = [UserRateThrottle]
    permission_classes = [IsAuthenticatedReadAdminManagementWrite]

    def get_serializer_class(self):
        if self.action not in ["list", "retrieve"]:
            return KeywordDetailSerializer
        return KeywordWriteSerializer
    http_method_names = ["get", "post", "patch", "delete"]