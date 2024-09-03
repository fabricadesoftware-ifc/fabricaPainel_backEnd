from django.core.mail import send_mail
from celery import shared_task

from django_project.settings import EMAIL_HOST_USER

from core.work.models import Work

@shared_task
def notify_advisor_on_data_update(work_id, accept_work_link, reject_work_link):
    work: object = Work.objects.get(id=work_id)

    subject: str = 'Dados atualizados'
    message: str = f'Olá {work.advisor}, o conteúdo do trabalho {work.title} foi alterado por {work.team}!\nPara aceitar a nova submissão clique no link: {accept_work_link}, para recusar clique aqui: {reject_work_link}'
    
    from_email: str = EMAIL_HOST_USER
    email_advisor_recipient_list: list[str] = [work.advisor.email]
    
    send_mail(subject, message, from_email, email_advisor_recipient_list)

