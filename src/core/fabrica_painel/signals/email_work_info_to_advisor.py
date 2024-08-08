import os
from uuid import uuid4
from dotenv import load_dotenv

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse

from core.fabrica_painel.tasks.send_email_advisor.send_work_email_to_advisor import send_work_email_to_advisor
from core.fabrica_painel.models import Work

load_dotenv()

@receiver(post_save, sender=Work)
def email_work_info_to_advisor(sender, instance: Work, created, **kwargs):

    if created:

        from_email: str = os.getenv("EMAIL_HOST_USER")
        email_recipient_list: list[str] = [instance.advisor.email]
        email_subject: str = f"{instance.edition} - Submissão de trabalho"
        
        token: str = str(uuid4())
        instance.verification_token = token
        instance.save()

        accept_work_path = reverse("accept-work",
                                   kwargs={"verification_token": token})
        accept_work_link = f"http://localhost:8000/{accept_work_path}"

        reject_work_path = reverse("reject-work",
                                      kwargs={"pk": instance.pk})
        reject_work_link = f"http://localhost:8000/{reject_work_path}"

        send_work_email_to_advisor.delay(instance.id, email_subject, from_email, email_recipient_list, accept_work_link, reject_work_link)

        