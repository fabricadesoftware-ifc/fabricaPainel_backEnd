from django.core.mail import send_mail
from django.utils.html import strip_tags
from core.work.infra.work_django_app.models import Work
from celery import shared_task

@shared_task
def send_work_email_to_advisor(work_id, email_subject, from_email, email_recipient_list, accept_work_link, students_emails):
    try:
        work = Work.objects.get(id=work_id)

        with open('src/templates/send_advisor_email_template.html', 'r') as file:
            html = file.read()

        html = html.replace("{{ work_title }}", work.title)
        fields_list = [field.name for field in work.field.all()]
        fields_string = ', '.join(fields_list)
        html = html.replace("{{ work_field }}", fields_string)
        html = html.replace("{{ work_abstract }}", work.abstract)

        if work.cross_cutting_theme:
            cross_theme_name = work.cross_cutting_theme.name
        else:
            cross_theme_name = "Nenhum tema transversal"
        html = html.replace("{{ work_cross_cutting_themes }}", cross_theme_name)
        html = html.replace("{{ accept_work_link }}", accept_work_link)       
        students_emails = [member.email for member in work.team.team_members.all()]
        if students_emails:
            students_emails_list = ', '.join(students_emails)
        else:
            students_emails_list = "Nenhum estudante na equipe"

        html = html.replace("{{ students_emails }}", str(students_emails_list))

        plain_message = strip_tags(html)

        send_mail(
            email_subject,
            plain_message,
            from_email,
            email_recipient_list,
            html_message=html,
            fail_silently=False,
        )

        print("Email enviado com sucesso")

    except Work.DoesNotExist:
        print("Work object not found.")
    except Exception as e:
        print(f"Erro ao enviar o email: {e}")
