from rest_framework.viewsets import ModelViewSet
from drf_spectacular.utils import extend_schema
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import CustomTokenObtainPairSerializer

from .models import User, Evaluator, Class, UserClass, Specialty
from .serializers import UserSerializer, EvaluatorSerializer, ClassSerializer, UserClassSerializer, UserViewSerializer, SpecialtySerializer
from .filters import UserFilter, EvaluatorFilter

from django_project.permissions import IsUserOwnerOrReadOnly, IsAdminOrReadOnly

@extend_schema(tags=["users"])
class UserViewSet(ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    filterset_class = UserFilter
    #permission_classes = [IsUserOwnerOrReadOnly]

@extend_schema(tags=["advisors"])
class AdvisorViewSet(ModelViewSet):
    queryset = User.objects.filter(is_advisor=True, user_type=User.TEACHER)
    serializer_class = UserSerializer
    http_method_names: list[str] = ["get"]
    filterset_class = UserFilter

@extend_schema(tags=["evaluators"])
class EvaluatorViewSet(ModelViewSet):
    queryset = Evaluator.objects.all()
    filterset_class = EvaluatorFilter
    serializer_class = EvaluatorSerializer
    http_method_names: list[str] = ["get", "post", "patch", "delete"]
    permission_classes = [IsAdminOrReadOnly]

@extend_schema(tags=["auth"])
class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
    
@extend_schema(tags=["classes"])
class ClassViewSet(ModelViewSet):
    queryset = Class.objects.all()
    serializer_class = ClassSerializer
    permission_classes = [IsAdminOrReadOnly]

@extend_schema(tags=["user_classes"])
class UserClassViewSet(ModelViewSet):
    queryset = UserClass.objects.all()
    serializer_class = UserViewSerializer
    http_method_names: list[str] = ["get", "post", "put", "delete"]
    permission_classes = [IsAdminOrReadOnly]

@extend_schema(tags=["specialties"])
class SpecialtyViewSet(ModelViewSet):
    queryset = Specialty.objects.all()
    serializer_class = SpecialtySerializer
    permission_classes = [IsAdminOrReadOnly]

