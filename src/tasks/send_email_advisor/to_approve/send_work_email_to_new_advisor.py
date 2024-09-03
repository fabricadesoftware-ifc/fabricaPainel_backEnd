from django.core.mail import send_mail
from celery import shared_task
from django_project.settings import EMAIL_HOST_USER
from core.work.models import Work
from core.user.models import User

@shared_task
def send_work_email_to_new_advisor(work_id, accept_work_link, reject_work_link, new_advisor_id):
    try:
        work: object = Work.objects.get(id=work_id)
        new_advisor_email: object = User.objects.get(id=new_advisor_id).email
        
    except Work.DoesNotExist:
        print("Work object not found.")
        return
    except User.DoesNotExist:
        print("New advisor object not found.")
        return
    except Exception as e:
        print(f"An error occurred: {e}")
        return

    email_subject: str = "Nova submissão de trabalho"
    print(f"New advisor email: {new_advisor_email}")
    email_recipient_list: list[str] = [new_advisor_email]
    from_email: str = EMAIL_HOST_USER

    email_message = f"""
    Título do Trabalho submetido:
    {work.title}
    Campo do Trabalho submetido:
    {work.field}
    Resumo do Trabalho submetido:
    {work.abstract}
    Para aceitar essa submissão, clique no seguinte link:
    {accept_work_link}
    """

    email_html_message = f"""
    <h2>Título do Trabalho submetido:</h2>
    <h3>{work.title}</h3>
    <h2>Campo do Trabalho submetido:</h2>
    <h3>{work.field}</h3>
    <h2>Resumo do Trabalho submetido:</h2>
    <h3>{work.abstract}</h3>
    Clique <a href="{accept_work_link}">aqui</a> para aceitar essa submissão
    Clique <a href="{reject_work_link}">aqui</a> para rejeitar essa submissão
    """

    try:
        send_mail(
            email_subject,
            email_message,
            from_email,
            email_recipient_list,
            html_message=email_html_message,
            fail_silently=False,
        )
        print("Email sent successfully.")
    except Exception as e:
        print(f"Failed to send email: {e}")