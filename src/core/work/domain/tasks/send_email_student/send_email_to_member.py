from django.core.mail import send_mail
from django_project.settings import EMAIL_HOST_USER
from celery import shared_task
from core.user.infra.user_django_app.models import User

@shared_task
def send_email_to_member(member, token):
    send_mail(
        'Convite para participar de um time',
        f'Olá {member.name}, você foi convidado para participar de um time. Para aceitar o convite, acesse o link: http://localhost:3000/accept-invite/{token}',
        EMAIL_HOST_USER,
        [member.email],
        fail_silently=False,
    )