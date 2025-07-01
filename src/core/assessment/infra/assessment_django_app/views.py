from rest_framework.viewsets import ModelViewSet
from drf_spectacular.utils import extend_schema

from core.assessment.infra.assessment_django_app.models import Assessment, Assessments, StudentAssessments
from core.assessment.infra.assessment_django_app.serializers import (
    AssessmentDetailSerializer,
    AssessmentWriteSerializer,
    StudentAssessmentsSerializer,
    StudentAssessmentsWriteSerializer
)
from core.assessment.infra.assessment_django_app.filters import AssessmentFilterSet, StudentAssessmentFilterSet
from django_project.permissions import IsAdvisorOrTeamMember

@extend_schema(tags=["assessment"])
class AssessmentViewSet(ModelViewSet):
    queryset = Assessment.objects.all()
    serializer_class = AssessmentDetailSerializer
    filterset_class = AssessmentFilterSet

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return AssessmentDetailSerializer
        return AssessmentWriteSerializer
    http_method_names = ["get", "post", "patch", "delete"]

class StudentAssessmentsViewSet(ModelViewSet):
    queryset = StudentAssessments.objects.all()
    permission_classes = [IsAdvisorOrTeamMember]
    filterset_class = StudentAssessmentFilterSet
    
    def get_queryset(self):
        user = self.request.user
        qs = super().get_queryset()

        if user.is_advisor:
            return qs.filter(work__advisor=user)
        return qs.filter(work__team__team_members=user)

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return StudentAssessmentsSerializer
        return StudentAssessmentsWriteSerializer
