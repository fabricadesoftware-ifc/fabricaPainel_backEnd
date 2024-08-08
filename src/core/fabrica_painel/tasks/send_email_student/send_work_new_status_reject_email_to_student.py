from django_project.settings import EMAIL_HOST_USER
from django.core.mail import send_mail
from celery import shared_task

from core.user.models import User

@shared_task
def send_work_new_status_reject_email_to_student(student_id):
    student = User.objects.get(id=student_id).email

    recipient_list = [student]
    from_email = EMAIL_HOST_USER
    email_message = """
    Olá, estudante!
    Seu trabalho teve o status mudado para rejeitado!
    """
    
    send_mail(
        "Seu trabalho que tinha sido aceito pelo seu orientador, mas agora o status foi alterado para rejeitado pelo Orientador.!",
        email_message,
        from_email,
        recipient_list,
    )














