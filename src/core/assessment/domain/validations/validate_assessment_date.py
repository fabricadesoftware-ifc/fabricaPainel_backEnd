from django.utils import timezone
from rest_framework import serializers


ASSESSMENT_PERIOD_FIELDS = {
    "work": ("initial_evaluators_date", "final_evaluators_date"),
    "student": ("initial_evaluators_date", "final_evaluators_date"),
}


def get_assessment_period(edition, target):
    initial_field, final_field = ASSESSMENT_PERIOD_FIELDS[target]
    return getattr(edition, initial_field, None), getattr(edition, final_field, None)


def _daily_window_error(edition, today, now_time):
    """
    Recorte diario de horario (ex.: avaliacao so das 8h as 22h). So vale pra
    avaliacao da banca (target="work") e so passa a restringir quando a
    edicao tiver pelo menos uma janela cadastrada — sem nenhuma cadastrada,
    mantem o comportamento antigo (dia todo, durante o periodo).
    """
    windows = edition.evaluation_daily_windows.all()
    if not windows.exists():
        return None

    window = windows.filter(date=today).first()
    if not window:
        return "Hoje nao e um dia de avaliacao para esta edicao."

    if not (window.opens_at <= now_time <= window.closes_at):
        opens = window.opens_at.strftime("%H:%M")
        closes = window.closes_at.strftime("%H:%M")
        return f"Avaliacoes hoje so podem ser feitas entre {opens} e {closes}."

    return None


def validate_assessment_date(work, target="work") -> bool:
    """
    Valida se a data (e, para a banca, o horario do dia) da avaliacao esta
    dentro do periodo permitido na edicao do trabalho.
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

    if target == "work":
        error = _daily_window_error(edition, today, timezone.localtime().time())
        if error:
            raise serializers.ValidationError(error)

    return True
