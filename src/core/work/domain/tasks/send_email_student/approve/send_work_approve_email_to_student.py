import os
from celery import shared_task
from django.utils.html import strip_tags
from django.core.mail import send_mail
from core.user.infra.user_django_app.models import User
from django_project.settings import BASE_DIR

@shared_task
def send_work_approve_email_to_student(from_email, students_ids, advisor_id):
    # Lê o template HTML do email
    with open(os.path.join(BASE_DIR, 'templates/send_work_aaprove_to_student_template.html'), 'r') as file:
        html = file.read()
    
    # Obtém os emails dos estudantes
    students_emails = list(User.objects.filter(id__in=students_ids).values_list('email', flat=True))

    # Obtém o email do orientador
    advisor_email = User.objects.get(id=advisor_id).email

    # Substitui o placeholder pelo email do orientador
    html = html.replace("{{ advisor_email }}", advisor_email)
    plain_message = strip_tags(html)

    # Verifica se há emails de estudantes
    if not students_emails:
        raise ValueError("Nenhum e-mail de estudante encontrado.")

    subject = "Trabalho submetido com sucesso!"
    
    # Envia o email para cada estudante
    for email in students_emails:
        send_mail(
            subject=subject,  # Corrigido: aqui está como argumento nomeado
            message=plain_message,  # Usando a mensagem em texto simples
            from_email=from_email, 
            recipient_list=[email],  # O campo 'to' é 'recipient_list'
            html_message=html,  # Inclui a versão em HTML
        )
