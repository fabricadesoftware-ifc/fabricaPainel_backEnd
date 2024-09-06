from django.core.mail import send_mail
from celery import shared_task

from core.user.infra.user_django_app.models import User

@shared_task
def send_work_new_status_approve_email_to_student(from_email, students_ids):
    students_emails = list(User.objects.filter(id__in=students_ids).values_list('email', flat=True))

    if not students_emails:
        raise ValueError("Nenhum e-mail de estudante encontrado.")

    email_message: str = """
    Olá, estudante!
    Seu trabalho teve o status mudado para aceito!
    """

    send_mail(
        "Seu trabalho que tinha sido rejeitado pelo seu orientador, mas agora o status foi alterado para aceito pelo Orientador.!",
        email_message,
        from_email,
        students_emails
    )














