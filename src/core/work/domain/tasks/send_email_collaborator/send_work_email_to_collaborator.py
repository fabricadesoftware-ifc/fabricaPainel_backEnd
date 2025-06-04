import os
from django.core.mail import send_mail
from django.utils.html import strip_tags
from core.work.infra.work_django_app.models import Work, WorkCollaborator
from celery import shared_task
from django_project.settings import BASE_DIR

@shared_task
def send_work_email_to_collaborator(work_collaborator_id, email_subject, from_email, accept_work_link, reject_work_link):
    try:
        work_collaborator = WorkCollaborator.objects.get(id=work_collaborator_id)
        work = work_collaborator.work
        
        print(f"Enviando email para o colaborador {work_collaborator.collaborator.email} (ID: {work_collaborator_id})")

        with open(os.path.join(BASE_DIR, 'templates/send_collaborator_email_template.html'), 'r', encoding='utf-8') as file:
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
        html = html.replace("{{ reject_work_link }}", reject_work_link)
        
        students_emails = [member.email for member in work.team.team_members.all()]
        if students_emails:
            students_emails_list = ', '.join(students_emails)
        else:
            students_emails_list = "Nenhum estudante na equipe"

        html = html.replace("{{ students_emails }}", str(students_emails_list))

        plain_message = strip_tags(html)

        # Envia email para o colaborador específico
        email_recipient_list = [work_collaborator.collaborator.email]

        send_mail(
            email_subject,
            plain_message,
            from_email,
            email_recipient_list,
            html_message=html,
            fail_silently=False,
        )

        print(f"Email enviado com sucesso para colaborador {work_collaborator.collaborator.email}")

    except WorkCollaborator.DoesNotExist:
        print("WorkCollaborator object not found.")
    except Exception as e:
        print(f"Erro ao enviar o email: {e}")
