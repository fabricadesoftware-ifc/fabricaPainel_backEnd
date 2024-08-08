
from django.core.mail import send_mail
from celery import shared_task

from core.user.models import User

@shared_task
def send_work_new_status_approve_email_to_student(from_email, student_id):
    student = User.objects.get(id=student_id)

    print("opa", student)
    recipient_list = [student]
    email_message = """
    Olá, estudante!
    Seu trabalho teve o status mudado para aceito!
    """

    send_mail(
        "Seu trabalho que tinha sido rejeitado pelo seu orientador, mas agora o status foi alterado para aceito pelo Orientador.!",
        email_message,
        from_email,
        recipient_list,
    )














