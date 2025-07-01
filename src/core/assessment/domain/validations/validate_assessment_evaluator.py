from rest_framework import serializers
from core.assessment.infra.assessment_django_app.models import Assessment

def validate_assessment_evaluator(owner, value):
    """
    Validates that the user creating the assessment is an advisor.
    """
    work = value.get('work', None)
    evaluator = value.get('evaluator', None)
    

    if not work.evaluator.filter(user=owner.id).exists():
        raise serializers.ValidationError(
            "O usuário deve ser um avaliador relacionado para criar uma avaliação."
        )
    
    if not evaluator == work.evaluator.get(user=owner.id):
        raise serializers.ValidationError(
            "Só pode avaliar trabalhos que o avaliador avaliou."
        )
    
    if Assessment.objects.filter(work=work, evaluator=evaluator).exists():
        raise serializers.ValidationError(
            "Já existe uma avaliação para este trabalho por este avaliador."
        )
        
    return value