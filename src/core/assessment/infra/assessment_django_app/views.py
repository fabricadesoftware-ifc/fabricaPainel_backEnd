from django.http import HttpResponse
from django.template import engines
from django.conf import settings
from rest_framework.viewsets import ModelViewSet
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import api_view, throttle_classes, permission_classes
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from rest_framework import status
from weasyprint import HTML
import tempfile
import os

from core.assessment.infra.assessment_django_app.models import Assessment, Assessments, StudentAssessments
from core.assessment.domain.assessment_datas import prepare_grades
from core.work.infra.work_django_app.models import Work
from core.user.infra.user_django_app.models import Evaluator
from core.assessment.infra.assessment_django_app.serializers import (
    AssessmentDetailSerializer,
    AssessmentWriteSerializer,
    StudentAssessmentsSerializer,
    StudentAssessmentsWriteSerializer
)
from core.assessment.infra.assessment_django_app.filters import AssessmentFilterSet, StudentAssessmentFilterSet
from django_project.permissions import IsAdvisorOrTeamMember, IsAdvisorOrEvaluatorOrTeamMember, IsTeacher, IsAdmin

@extend_schema(tags=["assessment"])
class AssessmentViewSet(ModelViewSet):
    queryset = Assessment.objects.all()
    permission_classes = [IsAdvisorOrEvaluatorOrTeamMember]
    filterset_class = AssessmentFilterSet
    
    def get_queryset(self):
        user = self.request.user
        qs = super().get_queryset()

        if Evaluator.objects.filter(user=user.id).exists():
            evaluator = Evaluator.objects.get(user=user.id)
            return qs.filter(work__evaluator=evaluator)
        if user.is_advisor:
            return qs.filter(work__advisor=user)
        return qs.filter(work__team__team_members=user)

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
    
@throttle_classes([UserRateThrottle])
@api_view(["GET"])
@permission_classes([IsTeacher, IsAdmin])
def generate_assessment_report(request, year, class_name=None):
    template_path = os.path.join(settings.BASE_DIR, "templates", "assessment_report.html")
    context = {
        "grades": prepare_grades(year, class_name),
    }
    with open(template_path, 'r', encoding='utf-8') as template_file:
        template_code = template_file.read()

    html_string = engines['django'].from_string(template_code).render(context)

    html = HTML(string=html_string)
    
    try:
        with tempfile.NamedTemporaryFile(delete=True) as tmp_file:
            html.write_pdf(tmp_file)
            tmp_file.seek(0)
            response = HttpResponse(tmp_file.read(), content_type="application/pdf")
            response["Content-Disposition"] = 'attachment; filename="assessment_report.pdf"'
            return response
    except Exception as e:
        return Response(
            {"error": f"Erro ao gerar o relatório: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )