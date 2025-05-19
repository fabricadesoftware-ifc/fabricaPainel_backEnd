from core.work.infra.work_django_app.models import Team
from rest_framework.exceptions import ValidationError
from datetime import datetime

def validate_team_members(data) -> str | bool:
    team_members = data.get('team_members')
    edition = data.get('edition')

    if not team_members:
        raise ValidationError("O campo 'team_members' é obrigatório")
    
    if not edition:
        raise ValidationError("O campo 'edition' é obrigatório")

    for member in team_members:
        if Team.objects.filter(team_members=member, edition=edition).exists():
            raise ValidationError(f"O membro {member.name} já está associado a outro time.")

    return False