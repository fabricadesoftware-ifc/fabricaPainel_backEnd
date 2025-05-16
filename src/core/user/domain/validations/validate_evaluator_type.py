from core.user.infra.user_django_app.models import User
from rest_framework.exceptions import ValidationError

def validate_evaluator_type(attrs):
    """
    Validates if the evaluator is a teacher.
    """
    evaluator = attrs.get('evaluator')

    if evaluator:
        if evaluator.user_type == User.STUDENT:
            raise ValidationError(f"O avaliador {evaluator} não pode ser um aluno")