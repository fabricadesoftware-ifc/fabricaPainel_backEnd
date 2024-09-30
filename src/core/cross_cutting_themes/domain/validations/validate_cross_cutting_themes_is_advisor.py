from core.user.infra.user_django_app.models import User

def validate_cross_cutting_themes_is_advisor():
    users = User.objects.filter(is_advisor=True)  # Usa filter() em vez de get() nessa bomba
    
    if not users.exists():  
        return False
    
    for user in users:
        if user.is_advisor:
            return True
    
    return False
