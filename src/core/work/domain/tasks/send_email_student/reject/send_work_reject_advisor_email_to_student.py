import os
from django.core.mail import send_mail
from celery import shared_task
from django.utils.html import strip_tags
from django_project.settings import BASE_DIR
from core.user.infra.user_django_app.models import User

@shared_task
def send_work_reject_advisor_email_to_student(from_email, students_ids):
    # Obtém os emails dos estudantes
    students_emails = list(User.objects.filter(id__in=students_ids).values_list('email', flat=True))

    if not students_emails:
        raise ValueError("Nenhum e-mail de estudante encontrado.")
    
    # Lê o template HTML do email
    with open(os.path.join(BASE_DIR, 'templates/send_work_reject_advisor_to_student_template.html'), 'r', encoding='utf-8') as file:
        html = file.read()
    
    plain_message = strip_tags(html)

    # Envia o email para cada estudante
    send_mail(
        subject="Orientador rejeitou orientar seu trabalho",
        message=plain_message,
        from_email=from_email,
        recipient_list=students_emails,
        html_message=html,
        fail_silently=False
    ) 