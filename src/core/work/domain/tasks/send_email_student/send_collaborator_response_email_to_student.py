from celery import shared_task
from django.core.mail import send_mail
from django.utils.html import strip_tags

from core.user.infra.user_django_app.models import User
from core.work.domain.tasks.email_branding import build_panel_email
from django_project.settings import EMAIL_HOST_USER


@shared_task
def send_collaborator_accept_email_to_student(students_ids, collaborator_id):
    students_emails = list(User.objects.filter(id__in=students_ids).values_list("email", flat=True))
    collaborator = User.objects.get(id=collaborator_id)
    collaborator_name = collaborator.name or collaborator.email

    if not students_emails:
        raise ValueError("Nenhum e-mail de estudante encontrado.")

    subject = "Colaborador aceitou participar do seu trabalho!"
    html = build_panel_email(
        "Colaborador aceitou participar",
        f"""
        <p style="margin:0 0 16px;">Olá, estudante!</p>
        <p style="margin:0 0 16px;">O colaborador <strong>{collaborator_name}</strong> aceitou participar do seu trabalho.</p>
        <p style="margin:0;color:#66788a;">Acompanhe o andamento da proposta pelo Painel de Integração.</p>
        """,
    )
    message = strip_tags(html)

    for email in students_emails:
        send_mail(
            subject=subject,
            message=message,
            from_email=EMAIL_HOST_USER,
            recipient_list=[email],
            html_message=html,
        )


@shared_task
def send_collaborator_reject_email_to_student(students_ids, collaborator_id):
    students_emails = list(User.objects.filter(id__in=students_ids).values_list("email", flat=True))
    collaborator = User.objects.get(id=collaborator_id)
    collaborator_name = collaborator.name or collaborator.email

    if not students_emails:
        raise ValueError("Nenhum e-mail de estudante encontrado.")

    subject = "Colaborador rejeitou participar do seu trabalho"
    html = build_panel_email(
        "Colaborador recusou o convite",
        f"""
        <p style="margin:0 0 16px;">Olá, estudante!</p>
        <p style="margin:0 0 16px;">O colaborador <strong>{collaborator_name}</strong> recusou o convite para participar do seu trabalho.</p>
        <div style="background:#fff8f8;border:1px solid #f2c7c7;border-radius:6px;padding:16px 18px;color:#7a3030;">Vocês podem convidar outro colaborador ou continuar o desenvolvimento conforme as regras da edição.</div>
        """,
    )
    message = strip_tags(html)

    for email in students_emails:
        send_mail(
            subject=subject,
            message=message,
            from_email=EMAIL_HOST_USER,
            recipient_list=[email],
            html_message=html,
        )
