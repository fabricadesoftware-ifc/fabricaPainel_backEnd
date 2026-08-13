from datetime import datetime
from django.utils.timezone import make_aware, get_current_timezone

from django_celery_beat.models import CrontabSchedule, PeriodicTask


def convert_date_to_datetime(date_str):
    """Converte uma string YYYY-MM-DD em datetime timezone-aware."""
    try:
        naive_dt = datetime.strptime(date_str, "%Y-%m-%d")
        return make_aware(naive_dt, timezone=get_current_timezone())
    except (ValueError, TypeError):
        return None


def create_remind_advisor_to_verify_invites_task(request):
    """Cria a tarefa periódica para lembrar os advisors de verificar os convites."""
    initial_advisor_acceptance = convert_date_to_datetime(
        request.data.get("initial_advisor_acceptance")
    )
    final_second_advisor_date = convert_date_to_datetime(
        request.data.get("final_second_advisor_date")
    )

    if not initial_advisor_acceptance or not final_second_advisor_date:
        print("Datas inválidas fornecidas.")
        raise ValueError("As datas fornecidas devem estar no formato YYYY-MM-DD.")

    print("Dados recebidos:", initial_advisor_acceptance, final_second_advisor_date)

    # Criação ou obtenção da agenda de execução
    schedule, _ = CrontabSchedule.objects.get_or_create(
        minute="0", hour="8", day_of_week="*", day_of_month="*", month_of_year="*"
    )

    # Criação ou atualização da tarefa periódica
    PeriodicTask.objects.update_or_create(
        name="Remind advisors to verify invites",
        defaults={
            "task": "core.work.domain.tasks.send_email_advisor.send_work_reminder_email.remind_advisor_to_verify_invites",
            "crontab": schedule,
            "enabled": True,
            "start_time": initial_advisor_acceptance,
            "expires": final_second_advisor_date,
        },
    )


def create_notify_advisors_grades_period_task(request):
    """Cria a tarefa periódica para notificar orientadores quando abrir o prazo de lançamento de notas."""
    initial_evaluators_date = convert_date_to_datetime(
        request.data.get("initial_evaluators_date")
    )
    final_evaluators_date = convert_date_to_datetime(
        request.data.get("final_evaluators_date")
    )

    if not initial_evaluators_date or not final_evaluators_date:
        print("Datas inválidas fornecidas para período de avaliadores.")
        raise ValueError("As datas fornecidas devem estar no formato YYYY-MM-DD.")

    # Criação ou obtenção da agenda de execução (diária às 8h)
    schedule, _ = CrontabSchedule.objects.get_or_create(
        minute="0", hour="8", day_of_week="*", day_of_month="*", month_of_year="*"
    )

    PeriodicTask.objects.update_or_create(
        name="Notify advisors about grade period opened",
        defaults={
            "task": "core.work.domain.tasks.send_email_advisor.send_grade_period_opened.notify_advisors_grade_period_opened",
            "crontab": schedule,
            "enabled": True,
            "start_time": initial_evaluators_date,
            "expires": final_evaluators_date,
        },
    )
