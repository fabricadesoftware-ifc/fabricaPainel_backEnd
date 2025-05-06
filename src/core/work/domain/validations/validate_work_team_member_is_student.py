from core.user.infra.user_django_app.models import User
from rest_framework.exceptions import ValidationError

def validate_work_team_member_is_student(attrs):
    team = attrs.get('team')

    if not team:
        raise ValidationError("Time não encontrado")

    team_members = team.team_members.all()

    for member in team_members:
        if member.user_type != User.STUDENT:
            raise ValidationError(f"O membro {member} não é estudante")

    return attrs
