from django.dispatch import receiver
from core.fabrica_painel.signals.signal_work_advisor_update import advisor_changed
from django.core.mail import send_mail
from asgiref.sync import sync_to_async
from django_project.settings import EMAIL_HOST_USER
from core.fabrica_painel.models.work import Work

@receiver(advisor_changed)
async def send_update_advisor_email_to_advisor(sender, instance, request, old_advisor, new_advisor, **kwargs):
    
    subject = 'Troca de Orientador no trabalho submetido pelo estudante: ' + str(instance.team)
    message = f"O orientador {old_advisor} foi trocado pelo novo orientador: {new_advisor} no trabalho: {instance.title}"

    from_email = EMAIL_HOST_USER
    recipient_list = [old_advisor, new_advisor]
    
    
    await sync_to_async(send_mail)(
        subject,
        message,
        from_email,
        recipient_list = recipient_list
    )

    
