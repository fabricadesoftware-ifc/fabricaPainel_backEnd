from django.core.mail import send_mail 
from celery import shared_task
from django_project.settings import EMAIL_HOST_USER


@shared_task
def send_forget_password_email(email, token):
    from_email = EMAIL_HOST_USER
    send_mail(
        'Password Reset',
        f'Your token is {token}',
        from_email,
        [email],
        fail_silently=False,
    )
    