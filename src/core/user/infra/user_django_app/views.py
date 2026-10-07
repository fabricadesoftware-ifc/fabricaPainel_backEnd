from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet
from drf_spectacular.utils import extend_schema
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import CustomTokenObtainPairSerializer

from core.user.domain.tasks.generate_certificates import generate_certificate_hash, generate_certificate_pdf
from core.user.domain.validations.validate_certificate_date import validate_certificate_date_is_valid
from core.work.infra.work_django_app.models import Team, Work, WorkCollaborator
from django.db.models import Q

from .models import User, Evaluator, Class, UserClass, Specialty, Certificate
from .serializers import UserPublicSerializer, UserSerializer, UserRetrieveSerializer, EvaluatorSerializer, ClassSerializer, UserClassSerializer, UserViewSerializer, SpecialtySerializer, CertificateSerializer
from .filters import UserFilter, EvaluatorFilter

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django_project.permissions import IsAdminOrReadOnly, IsAuthenticatedReadAdminManagementWrite, IsStudent
from django.http import FileResponse

def _is_privileged(user):
    return user.user_type == User.ADMIN or getattr(user, "is_management", False)


def _related_user_ids(user):
    team_ids = set(Team.objects.filter(team_members=user).values_list("id", flat=True))
    works = Work.objects.filter(
        Q(team_id__in=team_ids)
        | Q(advisor=user)
        | Q(evaluator__user=user)
        | Q(work_collaborator__collaborator=user)
    ).distinct()
    team_ids |= set(works.values_list("team_id", flat=True))

    ids = {user.id}
    ids.update(Team.team_members.through.objects.filter(team_id__in=team_ids).values_list("user_id", flat=True))
    ids.update(works.values_list("advisor_id", flat=True))
    ids.update(WorkCollaborator.objects.filter(work__in=works).values_list("collaborator_id", flat=True))
    ids.update(Work.evaluator.through.objects.filter(work__in=works).values_list("evaluator__user_id", flat=True))
    ids.discard(None)
    return ids


@extend_schema(tags=["users"])
class UserViewSet(ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    filterset_class = UserFilter
    permission_classes = [IsAuthenticatedReadAdminManagementWrite]

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return UserRetrieveSerializer
        if not _is_privileged(self.request.user):
            return UserPublicSerializer
        return UserSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if _is_privileged(user):
            return qs

        visible = Q(id__in=_related_user_ids(user))
        params = self.request.query_params
        if params.get("type") == "STUDENT" and params.get("registration"):
            visible |= Q(user_type=User.STUDENT, registration=params["registration"])
        if params.get("type") == "TEACHER":
            visible |= Q(user_type=User.TEACHER, is_advisor=True)
        return qs.filter(visible)

@extend_schema(tags=["advisors"])
class AdvisorViewSet(ModelViewSet):
    queryset = User.objects.filter(is_advisor=True, user_type=User.TEACHER)
    serializer_class = UserSerializer
    http_method_names: list[str] = ["get"]
    filterset_class = UserFilter
    permission_classes = [IsAuthenticatedReadAdminManagementWrite]

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
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = super().get_queryset()
        if user.user_type == User.ADMIN or user.is_management:
            return qs
        return qs.filter(user=user)
    
@extend_schema(tags=["certificate-generate"])
@api_view(['GET'])
@permission_classes([IsStudent])
def create_certificate(request, year):
    print(year)
    validate_certificate_date_is_valid(year)
    
    user = request.user
    work = Work.objects.get(team__team_members=user, edition__year=year)

    if work.status != Work.APPROVED:
        return Response({"error": "O trabalho não foi aprovado."}, status=400)

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
    
    
@extend_schema(tags=["certificate-verify"])
@api_view(['GET'])
@permission_classes([AllowAny])
def verify_certificate(request, hash_validate):
    try:
        certificate = Certificate.objects.get(
            hash_validate=hash_validate
        )
    except Certificate.DoesNotExist:
        return Response({"error": "Certificado não encontrado."}, status=404)

    return Response({
        "year": certificate.work.edition.year,
        "user": certificate.user.name,
        "work": certificate.work.title,
        "hash_validate": certificate.hash_validate
    })