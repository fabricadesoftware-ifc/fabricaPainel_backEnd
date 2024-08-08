from django.core.mail import send_mail
from celery import shared_task
from django_project.settings import EMAIL_HOST_USER
from core.user.models import User

@shared_task
def send_work_reject_email_to_student(student_id):
    student = User.objects.get(id=student_id).email
    
    email_message = """
    Olá, estudante!
    Seu trabalho foi rejeitado!
    """
    from_email = EMAIL_HOST_USER
    email_student_recipient_list = [student]

    send_mail(
        "Trabalho rejeitado pelo orientador!",
        email_message,
        from_email,
        email_student_recipient_list,
    )














