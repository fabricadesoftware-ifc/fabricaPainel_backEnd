from datetime import datetime, timedelta
from django_celery_beat.models import CrontabSchedule, PeriodicTask

def convert_date_to_datetime(date_str):
    """Converte uma string de data no formato YYYY-MM-DD para um objeto datetime."""
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        return None

def create_remind_advisor_to_verify_invites_task(request):
    """Cria a tarefa periódica para lembrar os advisors de verificar os convites"""
    initial_advisor_acceptance = convert_date_to_datetime(request.data.get("initial_advisor_acceptance", None))
    final_second_advisor_date = convert_date_to_datetime(request.data.get("final_second_advisor_date", None))

    """Cria a tarefa periódica para lembrar os advisors de verificar os convites"""
    schedule = CrontabSchedule.objects.get_or_create(
        minute="0",
        hour="15",
        day_of_week="*",
        day_of_month="*",
        month_of_year="*"
    )
    PeriodicTask.objects.get_or_create(
        name="Remind advisors to verify invites",
        task="core.work.domain.tasks.send_email_advisor.send_work_reminder_email.remind_advisor_to_verify_invites",
        crontab=schedule,
        enabled=True,
        start_time=initial_advisor_acceptance,
        expire=final_second_advisor_date,
    )