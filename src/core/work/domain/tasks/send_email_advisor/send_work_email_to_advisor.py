from django.core.mail import send_mail
from django.template.loader import render_to_string
from celery import shared_task

from core.work.infra.work_django_app.models import Work

@shared_task
def send_work_email_to_advisor(work_id, email_subject, from_email, email_recipient_list, accept_work_link, reject_work_link, students_emails):
    try:
        work = Work.objects.get(id=work_id)
        print("aqui dentro porra")
        # Renderiza o template HTML com as variáveis dinâmicas
        email_html_message = render_to_string('send_work_email_to_advisor.html', {
            'work_title': work.title,
            'work_field': work.field,
            'work_abstract': work.abstract,
            'work_cross_cutting_themes': work.cross_cutting_theme,
            'students_emails': students_emails,
            'accept_work_link': accept_work_link,
            'reject_work_link': reject_work_link
        })

        # Opcional: texto plano do email, caso o email client não suporte HTML
        email_message = f"""
        Título do Trabalho submetido: {work.title}
        Campo do Trabalho submetido: {work.field}
        Resumo do Trabalho submetido: {work.abstract}
        Estudantes envolvidos: {students_emails}
        Tema Transversai do Trabalho submetido: {work.cross_cutting_theme}
        Para aceitar essa submissão, clique no seguinte link: {accept_work_link}
        Para rejeitar essa submissão, clique no seguinte link: {reject_work_link}
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
