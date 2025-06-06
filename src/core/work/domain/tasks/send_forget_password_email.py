import os
from django.core.mail import send_mail
from celery import shared_task
from django_project.settings import EMAIL_HOST_USER, BASE_DIR
from django.utils.html import strip_tags

def safe_replace(html, placeholder, value):
    """Substitui placeholders de forma segura, tratando valores None ou vazios"""
    if value is None:
        value = ""
    return html.replace(placeholder, str(value))

@shared_task
def send_forget_password_email(email, token):
    from_email = EMAIL_HOST_USER
    
    # Renderizando o template HTML
    with open(os.path.join(BASE_DIR, 'templates/send_forget_password_email_template.html'), 'r', encoding='utf-8') as file:
        html = file.read()
        html = safe_replace(html, 'token', token)

    recipient_list = [email]
    
    subject = 'Recuperação de Senha'
    plain_message = strip_tags(html)
    send_mail(subject, plain_message, from_email, recipient_list, html_message=html)
    
    return "Email enviado com sucesso"