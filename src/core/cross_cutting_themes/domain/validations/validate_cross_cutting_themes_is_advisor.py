from django.core.exceptions import ObjectDoesNotExist
from core.user.infra.user_django_app.models import User

def validate_cross_cutting_themes_is_advisor():
    try:
        user = User.objects.get(is_advisor=True)
    except ObjectDoesNotExist:
        return False
    if user.is_advisor:
        return True
    return False
    
    
