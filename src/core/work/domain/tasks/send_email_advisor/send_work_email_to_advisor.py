from django.core.mail import send_mail
from django.utils.html import strip_tags
from core.work.infra.work_django_app.models import Work
from celery import shared_task


@shared_task
def send_work_email_to_advisor(work_id, email_subject, from_email, email_recipient_list, accept_work_link, reject_work_link, students_emails):
    try:
        # Obtém o objeto Work
        work = Work.objects.get(id=work_id)
        print("Dentro da tarefa de envio de email")

        # Lê o conteúdo do template HTML
        with open('src/templates/send_advisor_email_template.html', 'r') as file:
            html = file.read()

        # Substitui os placeholders no HTML
        html = html.replace("{{ work_title }}", work.title)

        # Obtém os campos relacionados
        fields_list = work.field.all().values_list('name', flat=True)  # Supondo que 'name' é o campo que você deseja mostrar
        fields_string = ', '.join(fields_list)  # Converte para uma string separada por vírgulas
        html = html.replace("{{ work_field }}", fields_string)
        html = html.replace("{{ work_abstract }}", work.abstract)

        if work.cross_cutting_theme:
            cross_theme_name = work.cross_cutting_theme.name
        else:
            cross_theme_name = "Nenhum tema transversal"
        html = html.replace("{{ work_cross_cutting_themes }}", cross_theme_name)
        html = html.replace("{{ accept_work_link }}", accept_work_link)
        html = html.replace("{{ reject_work_link }}", reject_work_link)

        print(work.team.team_members.all())
        students_emails = work.team.team_members.all().values_list('email', flat=True)
        students_emails_list = (students_emails)
        html = html.replace("{{ students_emails }}", ', '.join(students_emails_list)) 
       
        plain_message = strip_tags(html)

        print(plain_message)
        print(from_email)

        # Envia o email
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
