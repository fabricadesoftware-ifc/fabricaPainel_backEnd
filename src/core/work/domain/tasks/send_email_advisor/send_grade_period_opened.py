import os
from django.core.mail import send_mail
from django.utils.html import strip_tags
from celery import shared_task
from django_project.settings import EMAIL_HOST_USER, BASE_DIR

from core.edition.infra.edition_django_app.models import Edition
from core.work.infra.work_django_app.models import Work

from datetime import datetime


def safe_replace(html, placeholder, value):
    if value is None:
        value = ""
    return html.replace(placeholder, str(value))


@shared_task
def notify_advisors_grade_period_opened():
    """Envia email para orientadores informando que o prazo de lançamento de notas foi aberto."""
    current_year = datetime.now().year
    try:
        current_edition = Edition.objects.get(year=current_year)
    except Edition.DoesNotExist:
        return

    edition_works = Work.objects.filter(edition=current_edition)
    advisors_emails = edition_works.values_list("advisor__email", flat=True).distinct()

    from_email = EMAIL_HOST_USER
    for advisor_email in list(set(advisors_emails)):
        recipient_list = [advisor_email]

        works_to_notify = edition_works.filter(advisor__email=advisor_email)

        with open(
            os.path.join(BASE_DIR, "templates/send_advisor_grade_period_opened.html"),
            "r",
            encoding="utf-8",
        ) as file:
            html = file.read()

        titles = ""
        for work in works_to_notify:
            titles += f"<li>{work.title}</li>"

        html = safe_replace(html, "{{ work_list }}", titles)
        html = safe_replace(html, "{{ work_count }}", str(works_to_notify.count()))

        plain_message = strip_tags(html)

        subject = "Prazo para lançamento de notas aberto"

        send_mail(
            subject,
            plain_message,
            from_email,
            recipient_list,
            html_message=html,
            fail_silently=False,
        )
