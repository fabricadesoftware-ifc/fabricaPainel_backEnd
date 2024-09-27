from rest_framework.exceptions import ValidationError

def validate_work_max_and_min_members(attrs):
    team_members = attrs.get('team_members')

 
    if isinstance(team_members, list):
        num_members = len(team_members)
    else:
        num_members = team_members.count()  
    
    print(f"Quantidade de membros no time: {num_members}")
    
    if num_members > 7 or num_members < 4:
        raise ValidationError("O time não pode ter mais do que 7 membros e menos que 4")

    return attrs
