import os
from celery import shared_task
from django.core.mail import send_mail
from django.utils.html import strip_tags

from core.user.infra.user_django_app.models import User
from django_project.settings import EMAIL_HOST_USER, PAINEL_URL, BASE_DIR

@shared_task
def send_email_to_member(member_id, token, team):
    member = User.objects.get(id=member_id)
    
    with open(os.path.join(BASE_DIR, 'templates/send_email_to_member.template.html'), 'r') as file:
        html = file.read()

    link = f"{PAINEL_URL}/auth/accept-invite-team/{team}/{token}"
    recipient_list = [member.email]
    html = html.replace("{{ member.name }}", member.name)
    html = html.replace("{{ link }}", link)
    plain_message = strip_tags(html)
    
    send_mail(
        'Você foi convidado para um time!',
        plain_message,
        from_email=EMAIL_HOST_USER,
        recipient_list=recipient_list,
        html_message=html
    )