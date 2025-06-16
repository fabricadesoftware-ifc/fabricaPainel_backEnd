from datetime import datetime
from django.utils.timezone import make_aware, get_current_timezone
from django_celery_beat.models import ClockedSchedule, PeriodicTask
import json
from core.edition.infra.edition_django_app.models import Edition



def convert_date_to_datetime(date_str):
    """Converte uma string YYYY-MM-DD em datetime timezone-aware."""
    try:
        naive_dt = datetime.strptime(date_str, "%Y-%m-%d")
        date = make_aware(naive_dt, timezone=get_current_timezone())
        date = date.replace(hour=23, minute=59)
        return date
        
    except (ValueError, TypeError):
        return None

def create_work_expiration_tasks(request):
    """Cria duas tarefas únicas para expirar trabalhos em duas datas específicas."""
    #ver qual edição esta abarta

    final_advisor_acceptance = convert_date_to_datetime(request.data.get("final_advisor_acceptance"))
    final_second_advisor_date = convert_date_to_datetime(request.data.get("final_second_advisor_date"))

    if not final_advisor_acceptance or not final_second_advisor_date:
        print("Datas inválidas fornecidas.")
        return

    # 🔸 Criando a tarefa para a expiração da **primeira fase**
    clocked1, _ = ClockedSchedule.objects.get_or_create(clocked_time=final_advisor_acceptance)

    PeriodicTask.objects.create(
        clocked=clocked1,
        name=f'Expiração primeira fase - {final_advisor_acceptance.isoformat()}',
        task='core.work.domain.tasks.change_status.change_status_to_expired_works.change_status_to_expired',  # <<< Nome da task no Celery para primeira fase
        one_off=True,
        args=json.dumps([]),
        kwargs=json.dumps({}),
    )

    # 🔸 Criando a tarefa para a expiração da **segunda fase**
    clocked2, _ = ClockedSchedule.objects.get_or_create(clocked_time=final_second_advisor_date)

    PeriodicTask.objects.create(
        clocked=clocked2,
        name=f'Expiração segunda fase - {final_second_advisor_date.isoformat()}',
        task='core.work.domain.tasks.change_status.change_status_to_expired_works.change_status_to_expired',  # <<< Nome da task no Celery para segunda fase
        one_off=True,
        args=json.dumps([]),
        kwargs=json.dumps({}),
    )

    return 'Tarefas de expiração criadas com sucesso'
