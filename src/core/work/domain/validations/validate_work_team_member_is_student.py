from core.user.infra.user_django_app.models import User
from rest_framework.exceptions import ValidationError

def validate_work_team_member_is_student(attrs) -> str | bool:
    team_members = attrs.get('team_members')
    print(team_members)

    for member in team_members:
        if member.user_type != User.STUDENT:
            raise ValidationError(f"O membro {member} não é estudante")

    return False
