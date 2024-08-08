from django.core.mail import send_mail

from django_project.settings import EMAIL_HOST_USER
from core.fabrica_painel.models.work import Work
from core.user.models import User

from celery import shared_task

@shared_task
def send_update_advisor_email_to_advisor(work_id, old_advisor, new_advisor):
    work = Work.objects.get(id=work_id)
    new_advisor = User.objects.get(id=new_advisor).email
    old_advisor = User.objects.get(id=old_advisor).email

    subject = 'Troca de Orientador no trabalho submetido pelo estudante: ' + str(work.team)
    message = f"O orientador {old_advisor} foi trocado pelo novo orientador: {new_advisor} no trabalho: {work.title}"

    from_email = EMAIL_HOST_USER
    recipient_list = [old_advisor, new_advisor]
    
    send_mail(
        subject,
        message,
        from_email,
        recipient_list = recipient_list
    )

    
