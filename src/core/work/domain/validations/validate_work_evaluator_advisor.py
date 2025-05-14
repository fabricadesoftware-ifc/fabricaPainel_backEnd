from core.user.infra.user_django_app.models import User
from rest_framework.exceptions import ValidationError

def validate_work_team_member_is_student(attrs):
    evaluator = attrs.get('evaluator')
    co_advisor = attrs.get('co_advisor')

    if not evaluator:
        raise ValidationError("Time não encontrado")

    for evaluato in evaluator:
        if evaluato.user_type == User.STUDENT:
            raise ValidationError(f"O avaliador {evaluato} é estudante")
        
    if co_advisor:
        if co_advisor.user_type != User.TEACHER:
            raise ValidationError(f"O co-orientador {co_advisor} deve ser um professor")

    return attrs
