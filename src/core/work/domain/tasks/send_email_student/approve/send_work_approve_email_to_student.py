from django.core.mail import send_mail
from celery import shared_task

from core.user.infra.user_django_app.models import User

@shared_task
def send_work_approve_email_to_student(from_email, students_ids):
    students_emails = list(User.objects.filter(id__in=students_ids).values_list('email', flat=True))

    if not students_emails:
        raise ValueError("Nenhum e-mail de estudante encontrado.")

    email_message: str = """
    Olá, estudante!
    Seu trabalho foi submetido com sucesso!
    """
    send_mail(
        "Trabalho submetido com sucesso!",
        email_message,
        from_email,
        students_emails
    )
