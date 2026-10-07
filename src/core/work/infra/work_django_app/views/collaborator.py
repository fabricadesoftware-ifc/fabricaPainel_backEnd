from rest_framework.viewsets import ModelViewSet
from drf_spectacular.utils import extend_schema
from core.user.infra.user_django_app.models import User
from core.user.infra.user_django_app.serializers import UserSerializer
from core.user.infra.user_django_app.filters import UserFilter
from django_project.permissions import IsAuthenticatedReadAdminManagementWrite

@extend_schema(tags=["collaborators"])
class CollaboratorViewSet(ModelViewSet):
    # Filtra colaboradores que não são estudantes
    queryset = User.objects.filter(is_collaborator=True).exclude(user_type=User.STUDENT)
    serializer_class = UserSerializer
    http_method_names: list[str] = ["get"]
    filterset_class = UserFilter
    permission_classes = [IsAuthenticatedReadAdminManagementWrite]