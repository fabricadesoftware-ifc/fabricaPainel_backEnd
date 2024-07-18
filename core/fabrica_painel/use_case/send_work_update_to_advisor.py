import asyncio
from django.core.mail import send_mail
from django.dispatch import receiver
from core.fabrica_painel.signals.signal_work_update import data_updated
from core.fabrica_painel.models import Work
import os
from asgiref.sync import async_to_sync, sync_to_async

def send_email_to_update_on_advisor(subject, message, from_email, email_advisor_recipient_list):
    send_mail(subject, message, from_email, email_advisor_recipient_list)

@receiver(data_updated, sender=Work)
def notify_advisor_on_data_update(sender, instance, accept_work_link, **kwargs):
    subject = 'Dados atualizados'
    message = f'Olá {instance.advisor}, o conteúdo do trabalho {instance.title} foi atualizado por {instance.team}!\nPara aceitar a nova submissão clique no link: {accept_work_link}'
    
    from_email = os.getenv("EMAIL_HOST_USER")
    email_advisor_recipient_list = [instance.advisor.email]
    
    # Enviar e-mail assíncronamente
    async_to_sync(send_async_email)(subject, message, from_email, email_advisor_recipient_list)

@sync_to_async
def send_async_email(subject, message, from_email, email_advisor_recipient_list):
    send_email_to_update_on_advisor(subject, message, from_email, email_advisor_recipient_list)
