from core.edition.infra.edition_django_app.models import Edition
from rest_framework.exceptions import ValidationError
import datetime

def validate_work_date_submission_is_valid(attrs) -> str | bool:
    if 'edition' not in attrs:
        raise ValueError("A chave 'edition' não está presente em attrs")

    edition = Edition.objects.get(id=attrs['edition'].id)
    time_now = datetime.date.today()
    if time_now > edition.final_submission_date or time_now < edition.initial_submission_date:
        raise ValidationError("Fora da data de submissão")
    return False
