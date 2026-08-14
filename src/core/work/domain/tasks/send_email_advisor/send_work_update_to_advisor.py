import os
from django.core.mail import send_mass_mail
from django.utils import timezone
from django.utils.html import strip_tags
from celery import shared_task
from django_project.settings import EMAIL_HOST_USER, BASE_DIR
from core.work.infra.work_django_app.models import Work
from core.__seedwork.domain.actions.acceptance_window import acceptance_window_notice

def safe_replace(html, placeholder, value):
    """Substitui placeholders de forma segura, tratando valores None ou vazios"""
    if value is None:
        value = ""
    return html.replace(placeholder, str(value))

@shared_task
def notify_advisor_on_data_update(work_id, accept_work_link, reject_work_link):
    work = Work.objects.get(id=work_id)

    from_email = EMAIL_HOST_USER
    recipient_list = [work.advisor.email]

    with open(os.path.join(BASE_DIR, 'templates/send_work_update_email_to_advisor_template.html'), 'r', encoding='utf-8') as file:
        html = file.read()

    html = safe_replace(html, "{{ work_title }}", work.title)

    fields_list = work.field.all().values_list('name', flat=True)
    fields_string = ', '.join(fields_list) if fields_list else "Nenhum campo definido"
    html = safe_replace(html, "{{ work_field }}", fields_string)
    
    html = safe_replace(html, "{{ work_abstract }}", work.abstract)

    if work.cross_cutting_theme:
        cross_theme_name = work.cross_cutting_theme.name
    else:
        cross_theme_name = "Nenhum tema transversal"
    html = safe_replace(html, "{{ work_cross_cutting_themes }}", cross_theme_name)
    
    html = safe_replace(html, "{{ accept_work_link }}", accept_work_link)
    html = safe_replace(html, "{{ reject_work_link }}", reject_work_link)

    windows = [
        (work.edition.initial_submission_date, work.edition.final_submission_date),
        (work.edition.initial_second_submission_date, work.edition.final_second_submission_date),
    ]
    notice_html = acceptance_window_notice(timezone.localdate(), windows)
    html = safe_replace(html, "{{ acceptance_period_notice }}", notice_html)

    students_emails = work.team.team_members.all().values_list('email', flat=True)
    students_emails_list = list(students_emails)
    students_emails_string = ', '.join(students_emails_list) if students_emails_list else "Nenhum estudante na equipe"
    html = safe_replace(html, "{{ students_emails }}", students_emails_string)

    plain_message = strip_tags(html)

    subject = "Atualização do Trabalho: " + work.title

    send_mass_mail(
        subject,               
        plain_message,         
        from_email,            
        recipient_list,        
        html_message=html,     
        fail_silently=False,
    )
