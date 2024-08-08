from django.core.mail import send_mail
from celery import shared_task
from core.user.models import User

@shared_task
def send_work_approve_email_to_student(from_email, student_id):
    student = User.objects.get(id=student_id)

    recipient_list = [student]
    email_message = """
    Olá, estudante!
    Seu trabalho foi submetido com sucesso!
    """
    
    send_mail(
        "Trabalho submetido com sucesso!",
        email_message,
        from_email,
        recipient_list,
    )