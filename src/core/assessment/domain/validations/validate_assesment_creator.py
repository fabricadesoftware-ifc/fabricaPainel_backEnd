from rest_framework import serializers


def validate_assessment_creator(owner, value):
    """
    Validates that the user creating the assessment is an advisor.
    """
    work = value.get('work', None)
    student = value.get('student', None)
    print(f"Validating assessment creator: {owner}, work: {work}, student: {student}")
    
    if not work.advisor == owner:
        raise serializers.ValidationError(
            "O usuário deve ser o orientador relacionado para criar uma avaliação."
        )
    
    if not work.team.team_members.filter(id=student.id).exists():
        raise serializers.ValidationError(
            "O usuário deve ser membro da equipe relacionada para criar uma avaliação."
        )
    return value