from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from celery import shared_task

from django_project.settings import EMAIL_HOST_USER
from core.work.infra.work_django_app.models import Work

@shared_task
def notify_advisor_on_data_update(work_id, accept_work_link, reject_work_link):
    work = Work.objects.get(id=work_id)

    subject = 'Dados atualizados'
    advisor_name = work.advisor.name  # ou o campo que você usa para o nome do orientador
    work_title = work.title
    team_name = ', '.join([member.name for member in work.team.all()])  # ou o campo que você usa para o nome do membro da equipe
    
    # Renderizando o template HTML
    html_content = render_to_string('core/__seedwork/domain/templates/send_work_cancel_email_to_advisor.html', {
        'advisor_name': advisor_name,
        'work_title': work_title,
        'team_name': team_name,
        'accept_work_link': accept_work_link,
        'reject_work_link': reject_work_link,
    })

    from_email = EMAIL_HOST_USER
    email_advisor_recipient_list = [work.advisor.email]

    # Criando o e-mail
    email = EmailMultiAlternatives(subject, '', from_email, email_advisor_recipient_list)
    email.attach_alternative(html_content, "text/html")
    email.send()
