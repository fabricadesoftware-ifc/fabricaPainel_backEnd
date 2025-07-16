import os
from django.core.mail import send_mail
from django.utils.html import strip_tags
from celery import shared_task
from django_project.settings import EMAIL_HOST_USER, BASE_DIR

from core.edition.infra.edition_django_app.models import Edition
from core.work.infra.work_django_app.models import Work
from core.work.domain.value_objects import WorkAdvisorStatusType

from datetime import datetime

def safe_replace(html, placeholder, value):
    """Substitui placeholders de forma segura, tratando valores None ou vazios"""
    if value is None:
        value = ""
    return html.replace(placeholder, str(value))

@shared_task
def remind_advisor_to_verify_invites():   
    current_year = datetime.now().year
    current_edition = Edition.objects.get(year=current_year)
    edition_works = Work.objects.filter(edition=current_edition)
    pending_works = edition_works.filter(advisor_status=WorkAdvisorStatusType.Type.PENDING.value)
    pending_advisors = pending_works.values_list('advisor__email', flat=True).distinct()
    
    from_email = EMAIL_HOST_USER
    for advisor_email in list(set(pending_advisors)):

        recipient_list = [advisor_email]
        
        works_to_notify = pending_works.filter(advisor__email=advisor_email)

        with open(os.path.join(BASE_DIR, 'templates/send_work_reminder_advisor.html'), 'r', encoding='utf-8') as file:
            html = file.read()
            
        titles = ""
        for work in works_to_notify:
            titles += f"<li>{work.title}</li>"

        html = safe_replace(html, "{{ work_list }}", titles)
        html = safe_replace(html, "{{ work_count }}", str(works_to_notify.count()))

        plain_message = strip_tags(html)

        subject = "Lembrete de pedidos de orientação"

        send_mail(
            subject,               
            plain_message,         
            from_email,            
            recipient_list,        
            html_message=html,     
            fail_silently=False,
        )
