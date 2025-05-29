from uuid import uuid4
from django.urls import reverse
from django_project.settings import API_URL


def work_path(instance, **kwargs):
    token: str = str(uuid4())
    instance.verification_token = token
    instance.save()

    # Remove qualquer barra dupla do API_URL
    base_url = API_URL.rstrip('/')

    accept_work_path = reverse("accept-advisor-work", kwargs={"verification_token": token})
    reject_work_path = reverse("reject-advisor-work", kwargs={"verification_token": token})
    
    accept_work_link = f"{base_url}{accept_work_path}"
    reject_work_link = f"{base_url}{reject_work_path}"

    return accept_work_link, reject_work_link

def work_path_submission(instance, **kwargs):
    token: str = str(uuid4())
    instance.verification_token = token
    instance.save()

    # Remove qualquer barra dupla do API_URL
    base_url = API_URL.rstrip('/')

    accept_work_path = reverse("accept-submission", kwargs={"verification_token": token})
    reject_work_path = reverse("reject-submission", kwargs={"verification_token": token})
    
    accept_work_link = f"{base_url}{accept_work_path}"
    reject_work_link = f"{base_url}{reject_work_path}"

    return accept_work_link, reject_work_link