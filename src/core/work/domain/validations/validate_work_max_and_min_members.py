from rest_framework.exceptions import ValidationError
from core.edition.infra.edition_django_app.models import Edition

def validate_work_max_and_min_members(attrs) -> str | bool:
    team_members = getattr(attrs, 'team')

    edition = Edition.objects.get(is_open=True)
    
    if not edition:
        raise ValidationError("Nenhuma edição está aberta")

    members_min = edition.members_min
    members_max = edition.members_max

    if isinstance(team_members, list):
        num_members = len(team_members)
    else:
        num_members = team_members.count()  
    
    if num_members > members_max or num_members < members_min:
        raise ValidationError(f"O time não pode ter mais do que {members_max} membros e menos que {members_min}")

    return False
