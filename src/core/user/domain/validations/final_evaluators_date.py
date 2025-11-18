import hashlib
import logging
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.db.models import Prefetch
from django.db import transaction
from django.utils import timezone
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from datetime import datetime

from core.assessment.infra.assessment_django_app.models import Assessment, StudentAssessments
from core.user.infra.user_django_app.models import User, UserClass, Certificate
from core.work.infra.work_django_app.models import Work
from core.work.domain.value_objects import WorkStatusType
from core.edition.infra.edition_django_app.models import Edition

logger = logging.getLogger(__name__)


def validate_final_evaluators_date():

    # Busca edições onde o período de avaliação já passou
    now = timezone.now().date()
    editions_to_process = Edition.objects.filter(
        final_evaluators_date__lt=now
    ).select_related()

    if not editions_to_process.exists():
        logger.info("Nenhuma edição com período de avaliação finalizado encontrada.")
        return {
            "message": "Nenhuma edição para processar",
            "certificates_created": 0,
            "certificates_skipped": 0,
        }

    total_certificates_created = 0
    processing_details = []

    for edition in editions_to_process:
        logger.info(f"Processando edição {edition.year}...")

        # Busca trabalhos aprovados da edição com dados relacionados
        approved_works = (
            Work.objects.filter(
                edition=edition, status=WorkStatusType.Type.APPROVED.value
            )
            .select_related("team")
            .prefetch_related(
                "team__team_members",
                Prefetch("assessment_set", queryset=Assessment.objects.all()),
                Prefetch(
                    "studentassessments_set",
                    queryset=StudentAssessments.objects.select_related("student"),
                ),
            )
        )

        if not approved_works.exists():
            logger.info(
                f"Nenhum trabalho aprovado encontrado para edição {edition.year}"
            )
            continue

        edition_details = {
            "edition": edition.year,
            "works_processed": 0,
            "certificates_created": 0,
        }

        for work in approved_works:
            edition_details["works_processed"] += 1

            # Verifica se o trabalho tem avaliação válida
            work_assessment = work.assessment_set.first()
            if not work_assessment or work_assessment.grade <= 0:
                logger.warning(
                    f"Trabalho {work.id} - {work.title} não tem avaliação válida."
                )
                continue

            # Processa cada membro da equipe
            if work.team and work.team.team_members.exists():
                team_members = work.team.team_members.filter(user_type=User.STUDENT)

                for student in team_members:
                    if _process_student_certificate_validation(student, work, edition):
                        total_certificates_created += 1
                        edition_details["certificates_created"] += 1

        processing_details.append(edition_details)

    logger.info(
        f"Validação finalizada. Criados: {total_certificates_created} certificados"
    )

    return {
        "message": "Validação e geração de certificados finalizada com sucesso",
        "certificates_created": total_certificates_created,
        "processing_details": processing_details,
    }


def _process_student_certificate_validation(student, work, edition):
    # Verifica se já existe certificado (idempotência)
    existing_certificate = Certificate.objects.filter(user=student, work=work).first()
    if existing_certificate:
        logger.debug(f"Certificado já existe para {student.email} - Trabalho {work.id}")
        return False

    # Verifica se o estudante tem avaliação individual
    student_assessment = StudentAssessments.objects.filter(
        student=student, work=work
    ).first()

    if not student_assessment:
        logger.warning(
            f"Estudante {student.email} não tem avaliação individual para trabalho {work.id}"
        )
        return False

    # Verifica se as notas são válidas (maior que 0)
    if student_assessment.grade <= 0:
        logger.warning(
            f"Estudante {student.email} tem nota inválida: {student_assessment.grade}"
        )
        return False

    # Gera hash único para o certificado
    hash_validate = _generate_certificate_hash_validation(student, work, edition)

    # Cria o certificado
    try:
        with transaction.atomic():
            certificate = Certificate.objects.create(
                user=student, work=work, hash_validate=hash_validate
            )
            logger.info(
                f"Certificado criado para {student.email} - Trabalho: {work.title}"
            )
            return True

    except Exception as e:
        logger.error(f"Erro ao criar certificado para {student.email}: {str(e)}")
        return False

def _generate_certificate_hash_validation(student, work, edition):

    hash_data = f"{student.id}-{work.id}-{edition.id}-{timezone.now().timestamp()}"
    return hashlib.sha256(hash_data.encode()).hexdigest()


def validate_final_evaluators_date_for_edition(edition_id):

    try:
        edition = Edition.objects.get(id=edition_id)

        # Verifica se o período já passou
        now = timezone.now().date()
        if edition.final_evaluators_date >= now:
            return {
                "error": f"Período de avaliação da edição {edition.year} ainda não finalizou",
                "final_evaluators_date": edition.final_evaluators_date.isoformat(),
                "current_date": now.isoformat(),
            }

        # Processa apenas esta edição
        approved_works = (
            Work.objects.filter(
                edition=edition, status=WorkStatusType.Type.APPROVED.value
            )
            .select_related("team")
            .prefetch_related(
                "team__team_members",
                Prefetch("assessment_set", queryset=Assessment.objects.all()),
                Prefetch(
                    "studentassessments_set",
                    queryset=StudentAssessments.objects.select_related("student"),
                ),
            )
        )

        if not approved_works.exists():
            return {
                "message": f"Nenhum trabalho aprovado encontrado para edição {edition.year}",
                "certificates_created": 0,
            }

        total_created = 0

        for work in approved_works:
            work_assessment = work.assessment_set.first()
            if not work_assessment or work_assessment.grade <= 0:
                continue

            if work.team and work.team.team_members.exists():
                team_members = work.team.team_members.filter(user_type=User.STUDENT)

                for student in team_members:
                    if _process_student_certificate_validation(student, work, edition):
                        total_created += 1

        return {
            "message": f"Certificados validados e gerados para edição {edition.year}",
            "edition_year": edition.year,
            "certificates_created": total_created,
            "final_evaluators_date": edition.final_evaluators_date.isoformat(),
        }

    except Edition.DoesNotExist:
        return {"error": f"Edição {edition_id} não encontrada"}
    except Exception as e:
        logger.error(f"Erro ao validar certificados para edição {edition_id}: {str(e)}")
        return {"error": str(e)}
