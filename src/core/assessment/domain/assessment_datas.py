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
from core.user.infra.user_django_app.models import Class, UserClass
from core.edition.infra.edition_django_app.models import Edition
from core.work.infra.work_django_app.models import Work
from core.work.domain.value_objects import WorkStatusType


def prepare_grades(year, class_name=None):
    current_edition = Edition.objects.filter(year=year).first()    
    if not current_edition:
        raise ValueError(f"No edition found for year {year}")
    
    classes = Class.objects.all()
    if not classes:
        raise ValueError("No classes found in the system.")

    all_students = UserClass.objects.filter(year=year)
    if not all_students.exists():
        raise ValueError(f"No students found for year {year}")
    
    student_assessments = StudentAssessments.objects.filter(work__edition=current_edition)
    if not student_assessments.exists():
        raise ValueError(f"No student assessments found for year {year}")

    assessments = Assessment.objects.filter(work__edition=current_edition)
    if not assessments.exists():
        raise ValueError(f"No assessments found for year {year}")
    
    works = Work.objects.filter(edition=current_edition, status=WorkStatusType.Type.APPROVED.value)
    if not works.exists():
        raise ValueError(f"No approved works found for year {year}")
    
    grades = []
        
    if class_name != None:
        classes = classes.filter(name=class_name)
    
    for class_ in classes:
        class_grades = {
            'class': class_,
            'year': year,
            'students': []
        }
        students = all_students.filter(class_name=class_)
        for student in students:
            user = student.user
            student_grade = {
                    'student': user,
                    'average_score': None,
            }
            work = works.filter(team__team_members=user).first()
            if not work:
                student_grade['situation'] = 'Não Avaliado. Não há trabalho associado.'
                class_grades['students'].append(student_grade)
                continue

            student_grade['work_title'] = work.title
            student_grade['advisor'] = work.advisor
            student_grade['evaluator'] = work.evaluator.first()
            
            student_assessment = student_assessments.filter(student=user).first()
            work_assessment = assessments.filter(work=work).first()
            if not student_assessment:
                student_grade['situation'] = 'Pendente. Falta Avaliação do Orientador.'
                class_grades['students'].append(student_grade)
                continue
            
            if not work_assessment:
                student_grade['situation'] = 'Pendente. Falta Avaliação do Trabalho.'
                class_grades['students'].append(student_grade)
                continue
            
            total_score = work_assessment.grade + student_assessment.grade
            average_score = total_score / 2

            student_grade['average_score'] = average_score
            student_grade['situation'] = 'Aprovado' if average_score >= 6 else 'Reprovado'
            
            
            class_grades['students'].append(student_grade)
            
        grades.append(class_grades)
    return grades

