from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet
from drf_spectacular.utils import extend_schema
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import CustomTokenObtainPairSerializer

from core.user.domain.tasks.generate_certificates import generate_certificate_hash, generate_certificate_pdf
from core.work.infra.work_django_app.models import Work

from .models import User, Evaluator, Class, UserClass, Specialty, Certificate
from .serializers import UserSerializer, UserRetrieveSerializer, EvaluatorSerializer, ClassSerializer, UserClassSerializer, UserViewSerializer, SpecialtySerializer, CertificateSerializer
from .filters import UserFilter, EvaluatorFilter

from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django_project.permissions import IsUserOwnerOrReadOnly, IsAdminOrReadOnly, IsStudent
from django.http import FileResponse

@extend_schema(tags=["users"])
class UserViewSet(ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    filterset_class = UserFilter
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return UserRetrieveSerializer
        return UserSerializer
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
    
@extend_schema(tags=["certificate"])
class CertificateViewSet(ReadOnlyModelViewSet):
    queryset = Certificate.objects.all()
    serializer_class = CertificateSerializer
    filterset_fields = ["hash_validate"]
    
@extend_schema(tags=["certificate-generate"])
@api_view(['GET'])
@permission_classes([IsStudent])
def create_certificate(request, year):
    print(year)
    
    user = request.user
    work = Work.objects.filter(team__team_members=user, edition__year=year).first()
    
    if not work:
        return Response({"error": "O usuário não possui trabalho associado para o ano especificado."}, status=400)
    
    certificate, created = Certificate.objects.get_or_create(
        user=user,
        work=work,
        defaults={
            "hash_validate": generate_certificate_hash(user.id, work.id)
        }
    )
    
    pdf_file_path = generate_certificate_pdf(certificate, work, user)
    
    return FileResponse(
        open(pdf_file_path, 'rb'),
        content_type='application/pdf',
        as_attachment=True,
        filename=f"certificado_{user.id}.pdf"
    )