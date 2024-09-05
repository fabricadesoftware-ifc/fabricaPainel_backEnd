from django.urls import reverse
from uuid import uuid4

def create_paths_and_links(instance, token=None):
    if not token:
        token = str(uuid4())
    try:
        accept_work_path = reverse("accept-work",
                                   kwargs={"verification_token": token})
        accept_work_link = f"http://localhost:8000/{accept_work_path}"

        reject_work_path = reverse("reject-work",
                                      kwargs={"pk": instance.pk})
        reject_work_link = f"http://localhost:8000/{reject_work_path}"

        return accept_work_link, reject_work_link
    except Exception as e:
        return e