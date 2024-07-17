import os
from uuid import uuid4

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse
from dotenv import load_dotenv
from asgiref.sync import async_to_sync
from core.fabrica_painel.use_case.send_work_email_to_advisor import send_work_email_to_advisor
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

        async_to_sync(send_work_email_to_advisor)(instance, email_subject, from_email, email_recipient_list, accept_work_link)

        