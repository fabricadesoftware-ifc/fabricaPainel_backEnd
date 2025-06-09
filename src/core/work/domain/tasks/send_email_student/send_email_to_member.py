import os
from celery import shared_task
from django.core.mail import send_mail
from django.utils.html import strip_tags

from core.user.infra.user_django_app.models import User
from django_project.settings import EMAIL_HOST_USER, PAINEL_URL, BASE_DIR

def safe_replace(html, placeholder, value):
    """Substitui placeholders de forma segura, tratando valores None ou vazios"""
    if value is None:
        value = ""
    return html.replace(placeholder, str(value))

@shared_task
def send_email_to_member(member_id, token, team):
    member = User.objects.get(id=member_id)
    
    with open(os.path.join(BASE_DIR, 'templates/send_email_to_member.template.html'), 'r', encoding='utf-8') as file:
        html = file.read()

    link = f"{PAINEL_URL}/auth/accept-invite-team/{team}/{token}"
    recipient_list = [member.email]
    html = safe_replace(html, "{{ member.name }}", member.name or member.email)
    html = safe_replace(html, "{{ link }}", link)
    plain_message = strip_tags(html)
    
    send_mail(
        'Você foi convidado para um time!',
        plain_message,
        from_email=EMAIL_HOST_USER,
        recipient_list=recipient_list,
        html_message=html
    )