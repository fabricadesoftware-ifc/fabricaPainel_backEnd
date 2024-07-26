from rest_framework.viewsets import ModelViewSet
from drf_spectacular.utils import extend_schema
from django.urls import reverse
from uuid import uuid4

from core.fabrica_painel.models.work import Work
from core.fabrica_painel.serializers.work import (
    WorkDetailSerializer,
    WorkWriteSerializer
)

from core.fabrica_painel.tasks import notify_advisor_on_data_update
from core.fabrica_painel.tasks import send_update_advisor_email_to_advisor
from core.fabrica_painel.tasks import send_work_email_to_new_advisor

@extend_schema(tags=["work"])
class WorkViewSet(ModelViewSet):
    queryset = Work.objects.all()
    serializer_class = WorkDetailSerializer

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return WorkDetailSerializer
        return WorkWriteSerializer
    http_method_names = ["get", "post", "patch", "delete"]

    def update(self, request, *args, **kwargs):
        work = Work.objects.get(pk=self.kwargs["pk"])
        response = super().update(request, *args, **kwargs)
        old_advisor = work.advisor
        instance = self.get_object()
        new_advisor = instance.advisor

        if work.verification_token is not None and old_advisor != new_advisor:
            send_update_advisor_email_to_advisor.delay(
            instance.id,
            old_advisor.id,
            new_advisor.id
            )
            token = work.verification_token
            if token is not None:
                accept_work_path = reverse("accept-work",
                           kwargs={"verification_token": token})
                accept_work_link = f"http://localhost:8000{accept_work_path}"

                reject_work_path = reverse("reject-work",
                           kwargs={"pk": instance.pk})
                reject_work_link = f"http://localhost:8000{reject_work_path}"

          
            send_work_email_to_new_advisor.delay(
                work_id=instance.id,
                accept_work_link=accept_work_link,
                reject_work_link=reject_work_link,
                new_advisor_id=new_advisor.id
            )

        elif work.verification_token is None and work.final_submission_work_date is not None:
            token = str(uuid4())
            work.verification_token = token
            work.final_submission_work_date = None
            work.status = Work.WorkStatus.PENDING
            work.save()

            accept_work_path = reverse("accept-work",
                                        kwargs={"verification_token": token})
            accept_work_link = f"http://localhost:8000{accept_work_path}"

            reject_work_path = reverse("reject-work",
                                      kwargs={"pk": instance.pk})
            reject_work_link = f"http://localhost:8000/{reject_work_path}"

            notify_advisor_on_data_update.delay(instance.id, accept_work_link=accept_work_link, reject_work_link=reject_work_link)

        return response

        