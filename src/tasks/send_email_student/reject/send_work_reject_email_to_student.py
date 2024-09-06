from django.core.mail import send_mail
from celery import shared_task

from django_project.settings import EMAIL_HOST_USER
from core.user.infra.user_django_app.models import User

@shared_task
def send_work_reject_email_to_student(students_ids):
    students_emails = list(User.objects.filter(id__in=students_ids).values_list('email', flat=True))

    if not students_emails:
        raise ValueError("Nenhum e-mail de estudante encontrado.")
    
    email_message: str = """
    Olá, estudante!
    Seu trabalho foi rejeitado!
    """
    from_email: str = EMAIL_HOST_USER

    send_mail(
        "Trabalho rejeitado pelo orientador!",
        email_message,
        from_email,
        students_emails,
    )














