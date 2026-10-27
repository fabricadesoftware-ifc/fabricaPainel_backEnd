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
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from io import BytesIO
# from weasyprint import HTML
# import tempfile
import os
from django.db.models import Q

from core.assessment.infra.assessment_django_app.models import Assessment, Assessments, StudentAssessments
from core.assessment.domain.assessment_datas import prepare_grades
from core.assessment.domain.report_availability import grades_report_availability
from core.edition.infra.edition_django_app.models import Edition
from django_project.permissions import IsAdminOrManagement
from core.work.infra.work_django_app.models import Work
from core.user.infra.user_django_app.models import Evaluator
from core.user.domain.value_objects import UserType
from core.assessment.infra.assessment_django_app.serializers import (
    AssessmentDetailSerializer,
    AssessmentWriteSerializer,
    StudentAssessmentsSerializer,
    StudentAssessmentsWriteSerializer
)
from core.assessment.infra.assessment_django_app.filters import AssessmentFilterSet, StudentAssessmentFilterSet
from django_project.permissions import IsAdvisorOrTeamMember, IsAdvisorOrEvaluatorOrTeamMember, IsTeacherOrAdmin

@extend_schema(tags=["assessment"])
class AssessmentViewSet(ModelViewSet):
    queryset = Assessment.objects.all()
    permission_classes = [IsAdvisorOrEvaluatorOrTeamMember]
    filterset_class = AssessmentFilterSet
    
    def get_queryset(self):
        user = self.request.user
        qs = super().get_queryset()

        if user.user_type == UserType.Type.ADMIN:
            return qs

        # Cria uma condição OR para trabalhos onde o usuário é avaliador ou orientador
        conditions = Q()
        
        if Evaluator.objects.filter(user=user.id).exists():
            evaluator = Evaluator.objects.get(user=user.id)
            conditions |= Q(work__evaluator=evaluator)
            
        if user.is_advisor:
            conditions |= Q(work__advisor=user)
            
        if not conditions:  # Se não é nem avaliador nem orientador, filtra por membro da equipe
            return qs.filter(work__team__team_members=user)
            
        return qs.filter(conditions)

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return AssessmentDetailSerializer
        return AssessmentWriteSerializer
    http_method_names = ["get", "post", "patch", "delete"]

class StudentAssessmentsViewSet(ModelViewSet):
    queryset = StudentAssessments.objects.all()
    permission_classes = [IsAdvisorOrEvaluatorOrTeamMember]
    filterset_class = StudentAssessmentFilterSet
    
    def get_queryset(self):
        user = self.request.user
        qs = super().get_queryset()

        if user.user_type == UserType.Type.ADMIN:
            return qs
        if user.is_advisor:
            return qs.filter(work__advisor=user)
        return qs.filter(work__team__team_members=user)

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return StudentAssessmentsSerializer
        return StudentAssessmentsWriteSerializer
    
@api_view(["GET"])
@throttle_classes([UserRateThrottle])
@permission_classes([IsAdminOrManagement])
def generate_assessment_report(request, year, class_name=None):
    edition = Edition.objects.filter(year=year).first() if str(year).isdigit() else None
    if edition:
        availability = grades_report_availability(edition)
        if not availability["available"]:
            return Response(
                {
                    "error": availability["message"],
                    "available_after": availability["available_after"],
                },
                status=status.HTTP_403_FORBIDDEN,
            )

    try:
        grades = prepare_grades(int(year), class_name)
    except ValueError as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    styles = getSampleStyleSheet()
    style_normal = styles["BodyText"]
    style_header = styles["Heading1"]

    elements = []
    elements.append(Paragraph(f"Assessment Report — {year}{' — ' + class_name if class_name else ''}", style_header))
    elements.append(Spacer(1, 12))

    for class_block in grades:
        elements.append(Paragraph(f"Classe: {class_block['class'].name}", styles["Heading2"]))
        elements.append(Spacer(1, 6))

        data = [["Aluno", "Trabalho", "Média", "Situação"]]
        for s in class_block['students']:
            aluno = Paragraph(s.get('student', 'voce é incapaz'), style_normal)
            trabalho = Paragraph(s.get('work_title','N/A'), style_normal)
            media = Paragraph(f"{s.get('average_score','-'):0.2f}" if s.get('average_score') is not None else "-", style_normal)
            situacao = Paragraph(s['situation'], style_normal)
            data.append([aluno, trabalho, media, situacao])

        col_widths = [doc.width * 0.3, doc.width * 0.3, doc.width * 0.15, doc.width * 0.25]
        table = Table(data, colWidths=col_widths, repeatRows=1)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (2,1), (2,-1), 'CENTER'),
            ('ALIGN', (3,1), (3,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0,0), (-1,0), 8),
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.whitesmoke, colors.lightyellow]),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 12))

    doc.build(elements)
    buffer.seek(0)
    return FileResponse(buffer, as_attachment=True, filename="assessment_report.pdf")


@api_view(["GET"])
@throttle_classes([UserRateThrottle])
@permission_classes([IsAdminOrManagement])
def assessment_report_status(request, year):
    edition = Edition.objects.filter(year=year).first() if str(year).isdigit() else None
    if not edition:
        return Response({"error": f"No edition found for year {year}"}, status=status.HTTP_404_NOT_FOUND)

    return Response(grades_report_availability(edition))
