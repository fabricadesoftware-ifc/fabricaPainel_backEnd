from django.http import HttpResponse
from django.template import engines
from django.template.loader import render_to_string
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
from datetime import datetime

from core.assessment.infra.assessment_django_app.models import Assessment, StudentAssessments
from core.work.infra.work_django_app.models import Work
from core.work.domain.value_objects import WorkStatusType


def prepare_grades(year):
    works = Work.objects.filter(edition__year=year, status=WorkStatusType.Type.APPROVED.value)
    
    for work in works:        
        assessment = Assessment.objects.filter(work=work).first()
        members_display = []
        evaluators_display = []
        
        if assessment:
            work.grade = assessment.grade
        
        for member in work.team.team_members.all():
            student_assessment = StudentAssessments.objects.filter(student=member, work=work).first()
            grade = None
            
            if assessment and student_assessment:
                untreated_grade = student_assessment.grade
                grade = (untreated_grade + work.grade) / 2
                print(grade, untreated_grade, work.grade)
                
            members_display.append({
            "name": member.name or (member.user.get_full_name() if hasattr(member, "user") else "Sem nome"),
            "email": member.email,
            "grade": grade,
            })
            
        for evaluator in work.evaluator.all():
            evaluators_display.append(evaluator)
        
        work.student_assessments_display = members_display
        work.evaluators_display = evaluators_display
                    
    return works

