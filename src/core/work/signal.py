from uuid import uuid4
from django.db.models.signals import post_save
from django.dispatch import receiver

from core.work.models import Work


@receiver(post_save, sender=Work)
def signal_send_work_email_to_advisor(sender, instance: Work, created, **kwargs):
    if created:
        token: str = str(uuid4())
        instance.verification_token = token
        instance.save()
