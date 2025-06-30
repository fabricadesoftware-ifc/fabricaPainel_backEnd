import os
from celery import shared_task
from django.utils.html import strip_tags
from django.core.mail import send_mail
from core.user.infra.user_django_app.models import User
from django_project.settings import BASE_DIR, EMAIL_HOST_USER

@shared_task
def send_collaborator_accept_email_to_student(students_ids, collaborator_id):
    # Obtém os emails dos estudantes
    students_emails = list(User.objects.filter(id__in=students_ids).values_list('email', flat=True))

    # Obtém o nome do colaborador
    collaborator = User.objects.get(id=collaborator_id)
    collaborator_name = collaborator.name or collaborator.email

    if not students_emails:
        raise ValueError("Nenhum e-mail de estudante encontrado.")

    subject = "Colaborador aceitou participar do seu trabalho!"
    
    message = f"""
    Olá, estudante!
    
    Ótimas notícias! O colaborador {collaborator_name} aceitou participar do seu trabalho.
    
    Agora vocês podem começar a trabalhar juntos no desenvolvimento do projeto.
    
    Atenciosamente,
    Equipe Fábrica de Software
    """

    # Envia o email para cada estudante
    for email in students_emails:
        send_mail(
            subject=subject,
            message=message,
            from_email=EMAIL_HOST_USER,
            recipient_list=[email],
        )

@shared_task
def send_collaborator_reject_email_to_student(students_ids, collaborator_id):
    # Obtém os emails dos estudantes
    students_emails = list(User.objects.filter(id__in=students_ids).values_list('email', flat=True))

    # Obtém o nome do colaborador
    collaborator = User.objects.get(id=collaborator_id)
    collaborator_name = collaborator.name or collaborator.email

    if not students_emails:
        raise ValueError("Nenhum e-mail de estudante encontrado.")

    subject = "Colaborador rejeitou participar do seu trabalho"
    
    message = f"""
    Olá, estudante!
    
    Infelizmente o colaborador {collaborator_name} rejeitou o convite para participar do seu trabalho.
    
    Não desanimem! Vocês podem tentar convidar outro colaborador ou continuar o desenvolvimento do projeto.
    
    Atenciosamente,
    Equipe Fábrica de Software
    """

    # Envia o email para cada estudante
    for email in students_emails:
        send_mail(
            subject=subject,
            message=message,
            from_email=EMAIL_HOST_USER,
            recipient_list=[email],
        ) 