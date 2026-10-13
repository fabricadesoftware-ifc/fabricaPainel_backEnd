from core.assessment.infra.assessment_django_app.models import StudentAssessments
from rest_framework import serializers
from core.user.domain.value_objects import UserType


def validate_assessment_creator(owner, value, instance=None):
    work = value.get('work', None)
    student = value.get('student', None)

    # Admin registra a nota em nome do orientador (sem acesso ao sistema).
    is_admin = owner.user_type == UserType.Type.ADMIN

    if not is_admin and not work.advisor == owner:
        raise serializers.ValidationError(
            "O usuário deve ser o orientador relacionado para criar uma avaliação."
        )

    if not work.team.team_members.filter(id=student.id).exists():
        raise serializers.ValidationError(
            "O usuário deve ser membro da equipe relacionada para criar uma avaliação."
        )

    duplicates = StudentAssessments.objects.filter(work=work, student=student)
    if instance is not None:
        duplicates = duplicates.exclude(pk=instance.pk)

    if duplicates.exists():
        raise serializers.ValidationError(
            "Já existe uma avaliação para este aluno por este trabalho."
        )

    return value
