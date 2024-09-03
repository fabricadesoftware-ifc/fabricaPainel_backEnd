from django_project.settings import EMAIL_HOST_USER
from django.core.mail import send_mail
from celery import shared_task

from core.user.models import User

@shared_task
def send_work_new_status_reject_email_to_student(students_ids):
    students_emails = list(User.objects.filter(id__in=students_ids).values_list('email', flat=True))

    if not students_emails:
        raise ValueError("Nenhum e-mail de estudante encontrado.")
    
    from_email: str = EMAIL_HOST_USER
    email_message: str = """
    Olá, estudante!
    Seu trabalho teve o status mudado para rejeitado!
    """
    
    send_mail(
        "Seu trabalho que tinha sido aceito pelo seu orientador, mas agora o status foi alterado para rejeitado pelo Orientador.!",
        email_message,
        from_email,
        students_emails,
    )














