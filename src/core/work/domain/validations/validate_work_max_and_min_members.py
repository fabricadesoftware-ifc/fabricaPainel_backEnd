from rest_framework.exceptions import ValidationError

def validate_work_max_and_min_members(attrs) -> str | bool:
    team_members = attrs.get('team_members')
    edition = attrs.get('edition')

    if not team_members:
        raise ValidationError("O campo 'team_members' é obrigatório")
    
    if not edition:
        raise ValidationError("O campo 'edition' é obrigatório")

    members_min = edition.members_min
    members_max = edition.members_max

    if isinstance(team_members, list):
        num_members = len(team_members)
    else:
        num_members = team_members.count()  
    
    if num_members < members_min:
        raise ValidationError(f"O time deve ter no mínimo {members_min} membros")
    
    if num_members > members_max:
        raise ValidationError(f"O time deve ter no máximo {members_max} membros")

    return False
