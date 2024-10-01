from django.core.mail import send_mail
from django_project.settings import EMAIL_HOST_USER
from celery import shared_task
from core.user.infra.user_django_app.models import User
from django.utils.html import strip_tags


@shared_task
def send_email_to_member(member, token, team):

    with open('src/templates/send_email_to_member.template.html', 'r') as file:
        html = file.read()

    link = f"http://localhost:3000/auth/accept-invite-team/{team}/{token}"
    recipient_list = [member.email]
    html = html.replace("{{ member.name }}", member.name)
    html = html.replace("{{ link }}", link)
    plain_message = strip_tags(html)

    send_mail(
        plain_message,
        EMAIL_HOST_USER,
        message=plain_message, 
        from_email=EMAIL_HOST_USER, 
        recipient_list=recipient_list , 
        html_message=html,  
    )