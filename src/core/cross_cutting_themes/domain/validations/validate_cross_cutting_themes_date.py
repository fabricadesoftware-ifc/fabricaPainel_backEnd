from django.core.exceptions import ObjectDoesNotExist
from core.edition.infra.edition_django_app.models import Edition
from datetime import datetime

def validate_cross_cutting_themes_date_is_valid():
    try:
        edition = Edition.objects.get(is_open=True)
    except ObjectDoesNotExist:
        return False
    
    if edition.final_registration_theme_date < datetime.now().date():
        return True
    return False
