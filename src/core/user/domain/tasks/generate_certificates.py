import hashlib
from django.utils import timezone
from django.db import transaction
from celery import shared_task
from core.user.domain.validations.validate_certificates import CertificateValidations
from rest_framework.exceptions import ValidationError

from core.work.infra.work_django_app.models import Work
from core.assessment.infra.assessment_django_app.models import StudentAssessments, Assessment
from core.user.infra.user_django_app.models import User, Certificate
from core.user.domain.validations.validate_certificates import CertificateValidations  # assumindo o caminho


@shared_task
def generate_certificates_task():
    today = timezone.now().date()

    works = Work.objects.filter(edition__final_evaluators_date__lte=today)

    for work in works:

        if not Assessment.objects.filter(work=work, grade__isnull=False).exists():
            continue

        student_assessments = StudentAssessments.objects.filter(work=work)

        for sa in student_assessments:

            try:
                CertificateValidations.validate_student_assessment(sa.student, work)
                CertificateValidations.validate_final_evaluators_date(work)

            except ValidationError:
                continue  # pular este aluno se alguma validação falhar

            # Pular se já existe certificado
            if Certificate.objects.filter(user=sa.student, work=work).exists():
                continue

            # Se você tiver min_grade no Work, valida
            if hasattr(work, 'min_grade') and sa.grade < work.min_grade:
                continue

            # Gerar hash único e verificável
            raw = f"{sa.student.id}-{work.id}-{timezone.now().timestamp()}"
            certificate_hash = hashlib.sha256(raw.encode()).hexdigest()

            # Criar certificado de forma segura
            with transaction.atomic():
                Certificate.objects.create(
                    user=sa.student,
                    work=work,
                    hash_validate=certificate_hash,
                )