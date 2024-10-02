from django.core.mail import send_mail
from celery import shared_task
from django_project.settings import EMAIL_HOST_USER

@shared_task
def send_forget_password_email(email, token):
    from_email = EMAIL_HOST_USER
    
    # Renderizando o template HTML
    with open('src/templates/send_forget_password_email_template.html', 'r') as file:
        html_content = file.read()
        html_content = html_content.replace('token', token)

    recipient_list = [email]
    # Criando o e-mail
    subject = 'Recuperação de Senha'


    send_mail(subject, from_email, recipient_list, html_content)
    