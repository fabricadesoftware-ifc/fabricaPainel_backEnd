from uuid import uuid4
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse

from tasks import send_work_email_to_advisor
from core.work.models import Work
from django_project.settings import EMAIL_HOST_USER

@receiver(post_save, sender=Work)
def signal_send_work_email_to_advisor(sender, instance: Work, created, **kwargs):
    if created:
        
        token: str = str(uuid4())
        instance.verification_token = token
        instance.save()

        from_email: str = EMAIL_HOST_USER
        email_recipient_list: list[str] = [instance.advisor.email]
        students_emails = list(instance.team.team_members.values_list('email', flat=True))


        print(students_emails)

        email_subject: str = f"{instance.edition} - Submissão de trabalho"

        accept_work_path = reverse("accept-work",
                                   kwargs={"verification_token": token})
        accept_work_link = f"http://localhost:8000/{accept_work_path}"

        reject_work_path = reverse("reject-work",
                                      kwargs={"pk": instance.pk})
        reject_work_link = f"http://localhost:8000/{reject_work_path}"

        send_work_email_to_advisor.delay(instance.id, email_subject, from_email, email_recipient_list, accept_work_link, reject_work_link, students_emails)

        