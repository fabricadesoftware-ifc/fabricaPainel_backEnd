from core.work.infra.work_django_app.models import Team 
from rest_framework.exceptions import ValidationError


def validate_team_members(data) -> str | bool:
    team_members = data.get('team_members')

    if team_members:
        for member in team_members:
            if Team.objects.filter(team_members=member).exists():
                raise ValidationError(f"O membro {member.name} já está associado a outro time.")
    else:
        raise ValidationError("O campo 'team' é obrigatório.")
    return False