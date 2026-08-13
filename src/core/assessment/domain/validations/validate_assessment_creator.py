from core.assessment.infra.assessment_django_app.models import StudentAssessments
from rest_framework import serializers


def validate_assessment_creator(owner, value):
    work = value.get('work', None)
    student = value.get('student', None)

    if not work.advisor == owner:
        raise serializers.ValidationError(
            "O usuário deve ser o orientador relacionado para criar uma avaliação."
        )

    if not work.team.team_members.filter(id=student.id).exists():
        raise serializers.ValidationError(
            "O usuário deve ser membro da equipe relacionada para criar uma avaliação."
        )

    if StudentAssessments.objects.filter(work=work, student=student).exists():
        raise serializers.ValidationError(
            "Já existe uma avaliação para este aluno por este trabalho."
        )

    return value
