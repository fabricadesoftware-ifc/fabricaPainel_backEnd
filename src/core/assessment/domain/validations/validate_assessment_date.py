from core.edition.infra.edition_django_app.models import Edition
from django.utils import timezone
from rest_framework import serializers

def validate_assessment_date() -> bool:
    """
    Valida se a data da avaliação está dentro do período permitido para avaliações na edição.
    """
    today = timezone.localdate()
    edition = Edition.objects.filter(
        initial_evaluators_date__lte=today,
        final_evaluators_date__gte=today,
    ).first()
    if not edition:
        raise serializers.ValidationError("Nenhuma edição ativa encontrada.")

    if not edition.initial_evaluators_date or not edition.final_evaluators_date:
        raise serializers.ValidationError("Período de avaliação não definido para a edição ativa.")

    if not (edition.initial_evaluators_date <= today <= edition.final_evaluators_date):
        raise serializers.ValidationError(f"Avaliações só podem ser realizadas entre {edition.initial_evaluators_date} e {edition.final_evaluators_date}.")

    return True
