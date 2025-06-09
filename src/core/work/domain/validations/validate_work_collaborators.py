from rest_framework.exceptions import ValidationError
from core.work.infra.work_django_app.models import WorkCollaborator
from core.user.infra.user_django_app.models import User
from core.user.domain.validations import validate_user_can_be_collaborator
from datetime import datetime

def validate_work_collaborators(attrs):
    """
    Valida as regras de negócio para colaboradores:
    - Número mínimo e máximo de colaboradores por trabalho
    - Número máximo de trabalhos por colaborador
    - Colaborador deve ter is_collaborator=True
    - Colaborador não pode ser estudante (usando validação do domínio)
    - Verificar se está dentro do período de submissão
    """
    collaborators = attrs.get('collaborators', [])
    edition = attrs.get('edition')
    
    if not edition:
        raise ValidationError({"edition": "O campo 'edition' é obrigatório"})
    
    # Verificar se está dentro do período de submissão
    today = datetime.now().date()
    if edition.initial_submission_date and edition.final_submission_date:
        if today < edition.initial_submission_date or today > edition.final_submission_date:
            raise ValidationError({
                "collaborators": "Não é possível adicionar colaboradores fora do período de submissão"
            })
    
    # Se não há colaboradores, não precisa validar mais nada
    if not collaborators:
        return attrs
    
    # Validação do número de colaboradores
    num_collaborators = len(collaborators)
    
    if num_collaborators < edition.collaborators_min:
        raise ValidationError({
            "collaborators": f"O trabalho deve ter no mínimo {edition.collaborators_min} colaboradores"
        })
    
    if num_collaborators > edition.collaborators_max:
        raise ValidationError({
            "collaborators": f"O trabalho deve ter no máximo {edition.collaborators_max} colaboradores"
        })
    
    # Validação de que todos os colaboradores têm is_collaborator=True
    for collaborator in collaborators:
        if not collaborator.is_collaborator:
            raise ValidationError({
                "collaborators": f"O usuário {collaborator.name or collaborator.email} não é um colaborador válido"
            })
    
    # Validação usando o domínio user - colaboradores não podem ser estudantes
    for collaborator in collaborators:
        try:
            validate_user_can_be_collaborator(collaborator)
        except ValidationError as e:
            raise ValidationError({
                "collaborators": str(e)
            })
    
    # Validação do número máximo de trabalhos por colaborador
    for collaborator in collaborators:
        current_works_count = WorkCollaborator.objects.filter(
            collaborator=collaborator,
            status=1  # PENDING
        ).count() + WorkCollaborator.objects.filter(
            collaborator=collaborator,
            status=2  # APPROVED
        ).count()
        
        if current_works_count >= edition.works_per_collaborator_max:
            raise ValidationError({
                "collaborators": f"O colaborador {collaborator.name or collaborator.email} já atingiu o limite máximo de {edition.works_per_collaborator_max} trabalhos"
            })
    
    return attrs 