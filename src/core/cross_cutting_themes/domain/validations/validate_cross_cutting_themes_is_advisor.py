from core.user.infra.user_django_app.models import User

def validate_cross_cutting_themes_is_advisor(advisors: list[int]) -> bool:    
    for user in advisors:
        if not user.is_advisor:
            return True
    
    return False
