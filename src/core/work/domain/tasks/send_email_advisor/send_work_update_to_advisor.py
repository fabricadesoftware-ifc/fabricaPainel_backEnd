from django.core.mail import send_mail
from django.utils.html import strip_tags
from celery import shared_task

from django_project.settings import EMAIL_HOST_USER
from core.work.infra.work_django_app.models import Work

@shared_task
def notify_advisor_on_data_update(work_id, accept_work_link, reject_work_link):
    work = Work.objects.get(id=work_id)

    from_email = EMAIL_HOST_USER
    recipient_list = [work.advisor.email]

    print('DENTRO DESSA PORRA DE EMAIL')
    with open('src/templates/send_work_update_email_to_advisor_template.html', 'r') as file:
        html = file.read()

    html = html.replace("{{ work_title }}", work.title)

    fields_list = work.field.all().values_list('name', flat=True)
    fields_string = ', '.join(fields_list)
    html = html.replace("{{ work_field }}", fields_string)
    html = html.replace("{{ work_abstract }}", work.abstract)

    if work.cross_cutting_theme:
        cross_theme_name = work.cross_cutting_theme.name
    else:
        cross_theme_name = "Nenhum tema transversal"
    html = html.replace("{{ work_cross_cutting_themes }}", cross_theme_name)
    html = html.replace("{{ accept_work_link }}", accept_work_link)
    html = html.replace("{{ reject_work_link }}", reject_work_link)

    students_emails = work.team.team_members.all().values_list('email', flat=True)
    students_emails_list = list(students_emails)
    html = html.replace("{{ students_emails }}", ', '.join(students_emails_list))

    plain_message = strip_tags(html)

    print(plain_message)
    print(from_email)

    subject = "Atualização do Trabalho: " + work.title

    send_mail(
        subject,               
        plain_message,         
        from_email,            
        recipient_list,        
        html_message=html,     
        fail_silently=False,
    )
