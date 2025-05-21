from core.user.infra.user_django_app.models import User
from rest_framework.exceptions import ValidationError

def validate_cross_cutting_themes_is_advisor(advisors: list[int]) -> bool:    
    for user in advisors:
        if not user.is_advisor:
            raise ValidationError("Apenas os orientadores podem se inscrever nos temas transversais")
    
    return False
