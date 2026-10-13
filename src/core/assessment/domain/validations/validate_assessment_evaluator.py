from rest_framework import serializers
from core.assessment.infra.assessment_django_app.models import Assessment
from core.user.domain.value_objects import UserType

def validate_assessment_evaluator(owner, value, instance=None):
    """
    Validates that the user creating the assessment is an advisor.
    Em edicao (instance), a propria nota nao conta como duplicada.
    """
    work = value.get('work', None)
    evaluator = value.get('evaluator', None)
    

    if owner.user_type == UserType.Type.ADMIN:
        # Admin so registra a nota em nome de um avaliador JA atribuido ao
        # trabalho (professor sem acesso ao sistema); nao altera a banca.
        if evaluator is None or not work.evaluator.filter(pk=evaluator.pk).exists():
            raise serializers.ValidationError(
                "A nota só pode ser lançada em nome de um avaliador já atribuído ao trabalho."
            )
    else:
        if not work.evaluator.filter(user=owner.id).exists():
            raise serializers.ValidationError(
                "O usuário deve ser um avaliador relacionado para criar uma avaliação."
            )

        if not evaluator == work.evaluator.get(user=owner.id):
            raise serializers.ValidationError(
                "Só pode avaliar trabalhos que o avaliador avaliou."
            )
    
    duplicates = Assessment.objects.filter(work=work, evaluator=evaluator)
    if instance is not None:
        duplicates = duplicates.exclude(pk=instance.pk)

    if duplicates.exists():
        raise serializers.ValidationError(
            "Já existe uma avaliação para este trabalho por este avaliador."
        )
        
    return value
