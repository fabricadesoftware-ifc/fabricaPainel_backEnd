from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from celery import shared_task
from django_project.settings import EMAIL_HOST_USER

@shared_task
def send_forget_password_email(email, token):
    from_email = EMAIL_HOST_USER
    
    # Renderizando o template HTML
    html_content = render_to_string('core/__seedwork/domain/templates/send_forget_password_email.html', {
        'token': token,
    })

    # Criando o e-mail
    subject = 'Recuperação de Senha'
    email_message = EmailMultiAlternatives(subject, '', from_email, [email])
    email_message.attach_alternative(html_content, "text/html")
    email_message.send(fail_silently=False)
