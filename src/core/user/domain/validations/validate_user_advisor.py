from core.user.infra.user_django_app.models import User
from rest_framework.exceptions import ValidationError

def validate_user_can_be_advisor(user):
    """
    Valida se um usuário pode ser orientador.
    Apenas professores podem ser orientadores.
    """
    if user.user_type != User.TEACHER:
        raise ValidationError(
            f"O usuário {user.name or user.email} não pode ser orientador. "
            "Apenas professores podem ser orientadores."
        )

def validate_user_advisor_status(attrs):
    """
    Valida se um usuário pode ter o status de orientador ativado.
    Usado em serializers e forms.
    """
    user_type = attrs.get('user_type')
    is_advisor = attrs.get('is_advisor', False)
    
    if user_type == User.STUDENT and is_advisor:
        raise ValidationError({
            'is_advisor': 'Estudantes não podem ser orientadores. Apenas professores, administradores e TAE podem ser orientadores.'
        })

def validate_advisor_work_assignment(advisor):
    """
    Valida se um orientador pode ser atribuído a um trabalho.
    Verifica se tem is_advisor=True e é professor.
    """
    if not advisor.is_advisor:
        raise ValidationError(
            f"O usuário {advisor.name or advisor.email} não é um orientador válido."
        )
    
    if advisor.user_type != User.TEACHER:
        raise ValidationError(
            f"O orientador {advisor.name or advisor.email} deve ser um professor."
        ) 