import os

from django.db.models.signals import post_delete
from django.dispatch import receiver
from dotenv import load_dotenv
from asgiref.sync import async_to_sync
from core.fabrica_painel.use_case.send_work_delete_email_to_student import send_work_delete_email_to_student
from core.fabrica_painel.models import Work

load_dotenv()


@receiver(post_delete, sender=Work)
def signal_work_delete(sender, instance: Work, **kwargs):
    verification = instance.verification_token
    if verification is not None:
        print("Work was not accepted by advisor")
        return
    
    print("Sending email to student")
    from_email: str = os.getenv("EMAIL_HOST_USER")
    email_student_recipient_list: list[str] = [instance.team]

    async_to_sync(send_work_delete_email_to_student)(from_email, email_student_recipient_list, instance)
    

        