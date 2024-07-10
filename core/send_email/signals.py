import os
from uuid import uuid4

from django.core.mail import send_mail
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse
from dotenv import load_dotenv

from core.fabrica_painel.models import Work

load_dotenv()


@receiver(post_save, sender=Work)
def email_work_info_to_advisor(sender, instance: Work, created, **kwargs):
    """
    Create an use case so that the
        advisor receives an e-mail with all of the work info
            when a student submits the work.

    If the work is accepted by the advisor,
        initial_submission_work_date will be filled,
    otherwise,
        the submission will be rejected.
    """
    if created:
        print("YOU FOOL, YOU FELL FOR IT!")

        from_email: str = os.getenv("EMAIL_HOST_USER")
        email_recipient_list: list[str] = [instance.advisor.email]
        email_subject: str = f"{instance.edition} - Submissão de trabalho"

        token: str = str(uuid4())
        instance.verification_token = token
        instance.save()

        accept_work_path = reverse("accept-work",
                                   kwargs={"verification_token": token})
        accept_work_link = f"http://localhost:8000/{accept_work_path}"

        # Fallback to use when HTML message is not supported
        email_message: str = f"""
        Título do Trabalho submetido:
        {instance.title}
        Campo do Trabalho submetido:
        {instance.field}
        Resumo do Trabalho submetido:
        {instance.abstract}
        Para aceitar essa submissão, clique no seguinte link:
        {accept_work_link}
        """

        # Formatted message
        email_html_message: str = f"""
        <h2>Título do Trabalho submetido:</h2>
        <h3>{instance.title}</h3>
        <h2>Campo do Trabalho submetido:</h2>
        <h3>{instance.field}</h3>
        <h2>Resumo do Trabalho submetido:</h2>
        <h3>{instance.abstract}</h3>
        Clique <a href={accept_work_link}>aqui</a> para aceitar essa submissão
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

        except Exception as e:
            print(e)
