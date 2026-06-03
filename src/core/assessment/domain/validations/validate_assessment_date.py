from django.utils import timezone
from rest_framework import serializers


ASSESSMENT_PERIOD_FIELDS = {
    "work": ("initial_evaluators_date", "final_evaluators_date"),
    "student": ("initial_evaluators_date", "final_evaluators_date"),
}


def get_assessment_period(edition, target):
    initial_field, final_field = ASSESSMENT_PERIOD_FIELDS[target]
    return getattr(edition, initial_field, None), getattr(edition, final_field, None)


def validate_assessment_date(work, target="work") -> bool:
    """
    Valida se a data da avaliacao esta dentro do periodo permitido na edicao do trabalho.
    """
    if not work:
        raise serializers.ValidationError("Trabalho nao informado para avaliacao.")

    edition = work.edition
    initial_date, final_date = get_assessment_period(edition, target)
    today = timezone.localdate()

    if not initial_date or not final_date:
        raise serializers.ValidationError("Periodo de avaliacao nao definido para a edicao do trabalho.")

    if not (initial_date <= today <= final_date):
        raise serializers.ValidationError(
            f"Avaliacoes so podem ser realizadas entre {initial_date} e {final_date}."
        )

    return True
