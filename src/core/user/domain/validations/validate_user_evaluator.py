from core.user.infra.user_django_app.models import User
from rest_framework.exceptions import ValidationError

def validate_user_can_be_evaluator(user):
    """
    Valida se um usuário pode ser avaliador.
    Estudantes não podem ser avaliadores.
    """
    if user.user_type == User.STUDENT:
        raise ValidationError(
            f"O usuário {user.name or user.email} não pode ser avaliador. "
            "Apenas professores, administradores e TAE podem ser avaliadores."
        )

def validate_evaluator_creation(user):
    """
    Valida a criação de um novo avaliador.
    Verifica se o usuário não é estudante e se já não é avaliador.
    """
    # Verificar se não é estudante
    if user.user_type == User.STUDENT:
        raise ValidationError(
            'Estudantes não podem ser avaliadores. Apenas professores, administradores e TAE podem ser avaliadores.'
        )
    
    # Verificar se já é avaliador
    if hasattr(user, 'evaluator'):
        raise ValidationError(
            'Este usuário já é um avaliador.'
        ) 