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
        # Verifica se o membro está em um time com trabalho ativo (não rejeitado)
        active_teams = Team.objects.filter(
            team_members=member, 
            edition=edition
        ).exclude(work__status=4)  # Exclui trabalhos rejeitados
        
        if active_teams.exists():
            raise ValidationError(f"O membro {member.name} já está associado a outro time.")

    return False