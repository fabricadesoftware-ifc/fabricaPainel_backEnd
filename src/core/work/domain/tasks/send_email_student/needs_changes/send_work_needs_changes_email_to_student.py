import os
from django.core.mail import send_mail
from celery import shared_task
from django.utils.html import strip_tags
from django_project.settings import EMAIL_HOST_USER, BASE_DIR
from core.user.infra.user_django_app.models import User

@shared_task
def send_work_needs_changes_email_to_student(students_ids, message: str, work_title: str):
    students_emails = list(User.objects.filter(id__in=students_ids).values_list('email', flat=True))

    if not students_emails:
        raise ValueError("Nenhum e-mail de estudante encontrado.")
    
    with open(os.path.join(BASE_DIR, 'templates/send_needs_changes_to_work_template.html'), 'r') as file:
            html = file.read()
            
    html = html.replace("{{ title }}", 'Olá, estudante! Seu trabalho precisa de mudanças!')
    html = html.replace("{{ work_title }}", work_title)
    html = html.replace("{{ students_names }}", ', '.join(students_emails))
    html = html.replace("{{ changes }}", message)
    plain_message = strip_tags(html)
    
    from_email: str = EMAIL_HOST_USER

    send_mail(
        "Seu Orientador solicitou mudanças no seu trabalho!",
        plain_message,
        from_email,
        students_emails,
        html_message=html,
        fail_silently=False
    )














