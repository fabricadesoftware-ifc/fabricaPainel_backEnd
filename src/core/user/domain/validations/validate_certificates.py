import logging
from typing import Optional
from rest_framework.exceptions import ValidationError
from django.utils import timezone

from core.work.infra.work_django_app.models import Work
from core.edition.infra.edition_django_app.models import Edition
from core.assessment.infra.assessment_django_app.models import StudentAssessments
from core.user.infra.user_django_app.models import User

logger = logging.getLogger(__name__)

class CertificateValidations:

    @staticmethod
    def validate_final_evaluators_date(work: Work) -> Optional[str]:
        final_date = Edition.final_evaluators_date
        
        if final_date > timezone.now().date():
            raise ValidationError("The evaluator's final date has not passed yet.")
        return True
    
    @staticmethod
    def validate_student_assessment(student: User, work: Work) -> None:
        has_assessment = StudentAssessments.objects.filter(
            student=student,
            work=work,
            grade__isnull=False
        ).exists()

        if not has_assessment:
            raise ValidationError("The student has no valid assessment for this work.")
