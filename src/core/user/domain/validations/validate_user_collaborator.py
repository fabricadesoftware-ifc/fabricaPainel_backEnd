from core.user.infra.user_django_app.models import User
from rest_framework.exceptions import ValidationError

def validate_user_can_be_collaborator(user):
    """
    Valida se um usuário pode ser colaborador.
    Estudantes não podem ser colaboradores.
    """
    if user.user_type == User.STUDENT:
        raise ValidationError(
            f"O usuário {user.name or user.email} não pode ser colaborador. "
            "Apenas professores, administradores e TAE podem ser colaboradores."
        )

def validate_user_collaborator_status(attrs):
    """
    Valida se um usuário pode ter o status de colaborador ativado.
    Usado em serializers e forms.
    """
    user_type = attrs.get('user_type')
    is_collaborator = attrs.get('is_collaborator', False)
    
    if user_type == User.STUDENT and is_collaborator:
        raise ValidationError({
            'is_collaborator': 'Estudantes não podem ser colaboradores. Apenas professores, administradores e TAE podem ser colaboradores.'
        }) 