from uuid import uuid4
from django.urls import reverse


def work_path(instance, **kwargs):
  
    token: str = str(uuid4())
    instance.verification_token = token
    instance.save()

    accept_work_path = reverse("accept-work",
                                   kwargs={"verification_token": token})
    accept_work_link = f"http://localhost:8000/{accept_work_path}"

    return accept_work_link