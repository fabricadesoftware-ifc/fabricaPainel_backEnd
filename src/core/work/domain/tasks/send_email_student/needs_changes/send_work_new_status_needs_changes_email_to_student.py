from django_project.settings import EMAIL_HOST_USER
from django.core.mail import send_mail
from celery import shared_task
from django.utils.html import strip_tags

from core.user.infra.user_django_app.models import User

@shared_task
def send_work_new_status_needs_changes_email_to_student(students_ids, message: str, work_title: str):
    students_emails = list(User.objects.filter(id__in=students_ids).values_list('email', flat=True))

    if not students_emails:
        raise ValueError("Nenhum e-mail de estudante encontrado.")
 
    with open('src/templates/send_needs_changes_to_work_template.html', 'r') as file:
            html = file.read()
            
    html = html.replace("{{ title }}", 'Seu trabalho que tinha sido aceito pelo seu orientador, mas agora precisa de mudanças solicitadas pelo Orientador.!')
    html = html.replace("{{ work_title }}", work_title)
    html = html.replace("{{ students_names }}", ', '.join(students_emails))
    html = html.replace("{{ changes }}", message)
    plain_message = strip_tags(html)
    
    from_email: str = EMAIL_HOST_USER

    send_mail(
        "Seu trabalho que tinha sido aceito pelo seu orientador, mas agora precisa de mudanças solicitadas pelo Orientador.!",
        plain_message,
        from_email,
        students_emails,
        html_message=html,
        fail_silently=False
    )














