from django.core.mail import send_mail
from celery import shared_task
from django.template.loader import render_to_string
from core.work.infra.work_django_app.models import Work

@shared_task
def send_work_cancel_email_to_advisor(work_id: str, from_email: str) -> None:
    """
    Sends an email to the advisor informing that the work was canceled.
    """
    work = Work.objects.get(id=work_id)
    work_advisor = work.cross_cutting_theme.advisor.email

    subject = 'Trabalho cancelado'

    # Renderiza o template HTML
    context = {
        'work': work,
        'work_advisor': work_advisor,
    }
    email_html_message = render_to_string('src/core/__seedwork/domain/templates/send_work_cancel_email_to_advisor.html', context)

    email_advisor_recipient_list = [work_advisor]

    send_mail(
        subject,
        '',  # Deixe a mensagem de texto vazia
        from_email,
        email_advisor_recipient_list,
        html_message=email_html_message,
        fail_silently=False,
    )
