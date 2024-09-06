from django.core.mail import send_mail
from celery import shared_task
from core.work.infra.work_django_app.models import Work


@shared_task
def send_work_cancel_email_to_advisor(work_id: str, from_email: str) -> None:
    """
    Sends an email to the advisor informing that the work was canceled.
    """
    work: object = Work.objects.get(id=work_id)
    work_advisor: str = work.cross_cutting_theme.advisor

    subject: str = 'Trabalho cancelado'
    message : str = f'Olá {work.advisor}, o trabalho {work.title} foi cancelado pelos alunos {work.team}.'

    email_advisor_recipient_list: list = [work_advisor]

    send_mail(subject, message, from_email, email_advisor_recipient_list)
