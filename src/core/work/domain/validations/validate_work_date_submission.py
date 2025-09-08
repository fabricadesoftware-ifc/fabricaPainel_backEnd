from core.edition.infra.edition_django_app.models import Edition
from rest_framework.exceptions import ValidationError
import datetime
from django.utils import timezone


def validate_work_date_submission_is_valid(attrs) -> str | bool:
    if "edition" not in attrs:
        raise ValueError("A chave 'edition' não está presente em attrs")

    edition = Edition.objects.get(id=attrs["edition"].id)
    today = timezone.localdate()

    # Primeiro período (se ambos os limites existirem)
    first_ok = (
        getattr(edition, "initial_submission_date", None) is not None
        and getattr(edition, "final_submission_date", None) is not None
        and edition.initial_submission_date <= today <= edition.final_submission_date
    )

    # Segundo período (se ambos os limites existirem)
    second_ok = (
        getattr(edition, "initial_second_submission_date", None) is not None
        and getattr(edition, "final_second_submission_date", None) is not None
        and edition.initial_second_submission_date
        <= today
        <= edition.final_second_submission_date
    )

    if not (first_ok or second_ok):
        raise ValidationError("Fora da data de submissão")

    return False
