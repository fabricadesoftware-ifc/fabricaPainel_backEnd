from core.work.infra.work_django_app.models import Work
from rest_framework.exceptions import ValidationError

def validate_work_team_members(data) -> str | bool:
    team_members = data.get('team_members')
    
    if team_members:
        for member in team_members:
            if Work.objects.filter(team__team_members=member).exists():
                raise ValidationError(f"O membro {member.name} já está associado a outro trabalho.")
    else:
        raise ValidationError("O campo 'team' é obrigatório.")
    return False
