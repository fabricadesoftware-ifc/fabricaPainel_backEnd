from uuid import uuid4
from django.urls import reverse

from django_project.settings import API_URL


def work_path(instance, **kwargs):
  
    token: str = str(uuid4())
    instance.verification_token = token
    instance.save()

    accept_work_path = reverse("accept-work",
                                   kwargs={"verification_token": token})
    accept_work_link = f"{API_URL}/{accept_work_path}"

    return accept_work_link