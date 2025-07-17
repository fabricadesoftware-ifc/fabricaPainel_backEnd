from django.http import HttpResponse
from django.template import engines
from django.conf import settings
from django.http import FileResponse
from rest_framework.viewsets import ModelViewSet
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import api_view, throttle_classes, permission_classes
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from rest_framework import status
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from io import BytesIO
# from weasyprint import HTML
# import tempfile
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
# @permission_classes([IsTeacher, IsAdmin])
def generate_assessment_report(request, year, class_name=None):
        try:
            grades = prepare_grades(int(year), class_name)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        buffer = BytesIO()
        p = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4

        y = height - 50
        p.setFont("Helvetica-Bold", 14)
        p.drawString(50, y, f"Assessment Report - {year}{' - ' + class_name if class_name else ''}")
        y -= 30

        p.setFont("Helvetica", 10)
        for class_block in grades:
            p.drawString(50, y, f"Classe: {class_block['class'].name}")
            y -= 20

            for student in class_block['students']:
                text = f"{student['student'].get_full_name()} | Trabalho: {student.get('work_title','N/A')} | " \
                       f"Média: {student.get('average_score','-')} | Situação: {student['situation']}"
                if y < 50:
                    p.showPage()
                    y = height - 50
                    p.setFont("Helvetica", 10)
                p.drawString(60, y, text)
                y -= 15

            y -= 10  # espaço entre classes

        p.showPage()
        p.save()
        buffer.seek(0)
        return FileResponse(buffer, as_attachment=True, filename="assessment_report.pdf")