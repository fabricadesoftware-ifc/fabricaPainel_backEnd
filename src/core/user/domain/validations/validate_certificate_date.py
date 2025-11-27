from core.edition.infra.edition_django_app.models import Edition
from rest_framework.exceptions import ValidationError
import datetime
from django.utils import timezone

def validate_certificate_date_is_valid(year: int) -> str | bool:
    try:
        edition = Edition.objects.get(year=year)
    except Edition.DoesNotExist:
        raise ValidationError(f"Edição para o ano {year} não encontrada")

    today = timezone.localdate()

    if edition.final_event_date > today:
        raise ValidationError("Certificado ainda não disponível")
    
    return