from celery import shared_task
from django.core.mail import send_mail
from django.utils.html import strip_tags

from core.user.infra.user_django_app.models import User
from core.work.domain.tasks.email_branding import build_panel_email


@shared_task
def send_work_new_status_approve_email_to_student(from_email, students_ids):
    students_emails = list(User.objects.filter(id__in=students_ids).values_list("email", flat=True))

    if not students_emails:
        raise ValueError("Nenhum e-mail de estudante encontrado.")

    html = build_panel_email(
        "Status alterado para aceito",
        """
        <p style="margin:0 0 16px;">Olá, estudante!</p>
        <p style="margin:0;">Seu trabalho teve o status alterado para <strong>aceito</strong> pelo orientador.</p>
        """,
    )

    send_mail(
        "Seu trabalho foi alterado para aceito pelo orientador",
        strip_tags(html),
        from_email,
        students_emails,
        html_message=html,
    )
