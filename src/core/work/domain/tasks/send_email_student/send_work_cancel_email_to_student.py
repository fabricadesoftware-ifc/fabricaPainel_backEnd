from celery import shared_task
from django.core.mail import send_mail
from django.utils.html import strip_tags

from core.work.domain.tasks.email_branding import build_panel_email
from core.work.infra.work_django_app.models import Work


@shared_task
def send_work_cancel_email_to_student(work_id: str, from_email: str) -> None:
    work = Work.objects.get(id=work_id)
    students = work.team.team_members.all()
    students_emails = [student.email for student in students]

    html = build_panel_email(
        "Trabalho cancelado",
        f"""
        <p style="margin:0 0 16px;">Olá, estudante!</p>
        <p style="margin:0;">O trabalho <strong>{work.title}</strong> foi cancelado com sucesso.</p>
        """,
    )

    send_mail(
        "Trabalho cancelado com sucesso.",
        strip_tags(html),
        from_email,
        students_emails,
        html_message=html,
    )
