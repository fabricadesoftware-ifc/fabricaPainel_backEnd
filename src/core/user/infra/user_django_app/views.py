from rest_framework.viewsets import ModelViewSet
from drf_spectacular.utils import extend_schema
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import CustomTokenObtainPairSerializer

from .models import User, Evaluator
from .serializers import UserSerializer, EvaluatorSerializer
from .filters import UserFilter, EvaluatorFilter

@extend_schema(tags=["users"])
class UserViewSet(ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    filterset_class = UserFilter

@extend_schema(tags=["advisors"])
class AdvisorViewSet(ModelViewSet):
    queryset = User.objects.filter(is_advisor=True)
    serializer_class = UserSerializer
    http_method_names: list[str] = ["get"]
    filterset_class = UserFilter

@extend_schema(tags=["evaluators"])
class EvaluatorViewSet(ModelViewSet):
    queryset = Evaluator.objects.all()
    filterset_class = EvaluatorFilter
    serializer_class = EvaluatorSerializer
    http_method_names: list[str] = ["get"]


@extend_schema(tags=["auth"])
class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
