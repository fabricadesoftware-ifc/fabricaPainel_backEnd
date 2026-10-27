from datetime import timedelta

from django.utils import timezone


def grades_report_release_date(edition):
    """Relatório de notas libera no dia seguinte ao fim do evento."""
    if not edition.final_event_date:
        return None
    return edition.final_event_date + timedelta(days=1)


def grades_report_availability(edition) -> dict:
    release_date = grades_report_release_date(edition)
    if not release_date:
        return {
            "available": False,
            "available_after": None,
            "message": "A edição não possui data final do evento.",
        }

    if timezone.localdate() < release_date:
        return {
            "available": False,
            "available_after": release_date.isoformat(),
            "message": f"Relatório de notas disponível a partir de {release_date.strftime('%d/%m/%Y')}.",
        }

    return {
        "available": True,
        "available_after": release_date.isoformat(),
        "message": None,
    }
