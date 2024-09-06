from django.core.mail import send_mail
from celery import shared_task

from core.work.infra.work_django_app.models import Work

@shared_task
def send_work_email_to_advisor(work_id, email_subject, from_email, email_recipient_list, accept_work_link, reject_work_link, students_emails):
    try:
        work: object = Work.objects.get(id=work_id)        

        email_message: str = f"""
        Título do Trabalho submetido:
        {work.title}
        Campo do Trabalho submetido:
        {work.field}
        Resumo do Trabalho submetido:
        {work.abstract}
        Estudantes envolvidos:
        {students_emails}
        Para aceitar essa submissão, clique no seguinte link:
        {accept_work_link}
        """

        email_html_message: str = f"""
        <h2>Título do Trabalho submetido:</h2>
        <h3>{work.title}</h3>
        <h2>Campo do Trabalho submetido:</h2>
        <h3>{work.field}</h3>
        <h2>Resumo do Trabalho submetido:</h2>
        <h3>{work.abstract}</h3>
        <h2>Estudantes envolvidos:</h2>
        <h3>{students_emails}</h3>
        Clique <a href="{accept_work_link}">aqui</a> para aceitar essa submissão
        Clique <a href="{reject_work_link}">aqui</a> para rejeitar essa submissão
        """
        send_mail(
            email_subject,
            email_message,
            from_email,
            email_recipient_list,
            html_message=email_html_message,
            fail_silently=False,
        )

    except Work.DoesNotExist:
        print("Work object not found.")
    except Exception as e:
        print(e)