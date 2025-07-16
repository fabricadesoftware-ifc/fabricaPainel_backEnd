from django.http import HttpResponse
from django.template import engines
from django.template.loader import render_to_string
from django.conf import settings
from django.db.models import Prefetch
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

    # 1. Seleciona estudantes com dados relacionados de user e class de forma eficiente
    all_students = (
        UserClass.objects.filter(year=year)
        .select_related("user", "class_name")
    )
    if not all_students.exists():
        raise ValueError(f"No students found for year {year}")

    # 2. Carrega os trabalhos aprovados relacionados à edição, com advisor e evaluators
    works_qs = (
        Work.objects.filter(edition=current_edition, status=WorkStatusType.Type.APPROVED.value)
        .select_related("advisor", "edition")
        .prefetch_related(
            Prefetch("team__team_members", to_attr="members"),
            Prefetch("evaluator", to_attr="evaluators"),
        )
    )
    if not works_qs.exists():
        raise ValueError(f"No approved works found for year {year}")

    # 3. Carrega as avaliações de estudantes e trabalhos, incluindo relações importantes
    student_assessments_qs = (
        StudentAssessments.objects.filter(work__edition=current_edition)
        .select_related("student", "work")
    )
    if not student_assessments_qs.exists():
        raise ValueError(f"No student assessments found for year {year}")

    assessments_qs = (
        Assessment.objects.filter(work__edition=current_edition)
        .select_related("work", "evaluator")
    )
    if not assessments_qs.exists():
        raise ValueError(f"No assessments found for year {year}")

    # 4. Filtra classes se necessário
    classes = Class.objects.all()
    if class_name:
        classes = classes.filter(name=class_name)
    if not classes.exists():
        raise ValueError("No classes found in the system.")

    grades = []

    # Cria dicionários precalculados: mapa do aluno → avaliação, trabalho → avaliação
    student_assessment_map = {
        sa.student_id: sa for sa in student_assessments_qs
    }
    work_assessment_map = {
        assess.work_id: assess for assess in assessments_qs
    }

    # Itera pelas classes
    for class_ in classes:
        class_grades = {'class': class_, 'year': year, 'students': []}
        students = all_students.filter(class_name=class_)
        for uc in students:
            user = uc.user
            entry = {'student': user, 'average_score': None}

            # Procura trabalho na lista em memória → sem query adicional
            work = next((w for w in works_qs if user in w.team.members), None)
            if not work:
                entry['situation'] = 'Não Avaliado. Não há trabalho associado.'
                class_grades['students'].append(entry)
                continue

            entry.update({
                'work_title': work.title,
                'advisor': work.advisor,
                'evaluator': work.evaluators[0] if work.evaluators else None,
            })

            sa = student_assessment_map.get(user.id)
            wa = work_assessment_map.get(work.id)

            if not sa:
                entry['situation'] = 'Pendente. Falta Avaliação do Orientador.'
            elif not wa:
                entry['situation'] = 'Pendente. Falta Avaliação do Trabalho.'
            else:
                avg = (sa.grade + wa.grade) / 2
                entry['average_score'] = avg
                entry['situation'] = 'Aprovado' if avg >= 6 else 'Reprovado'

            class_grades['students'].append(entry)

        grades.append(class_grades)

    return grades