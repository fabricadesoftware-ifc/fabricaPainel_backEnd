from django.core.exceptions import ObjectDoesNotExist
from rest_framework.exceptions import ValidationError
from core.edition.infra.edition_django_app.models import Edition
from datetime import datetime


def validate_cross_cutting_themes_date_is_valid():
    try:
        edition = Edition.objects.get(is_active=True)
    except ObjectDoesNotExist:
        return False

    if edition.final_registration_theme_date < datetime.now().date():
        raise ValidationError("Fora da data de inscrição de temas transversais")
    return False
