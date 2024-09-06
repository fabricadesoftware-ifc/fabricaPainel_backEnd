from rest_framework.viewsets import ModelViewSet
from drf_spectacular.utils import extend_schema
from uuid import uuid4
from rest_framework import status
from rest_framework.response import Response

from core.work.infra.work_django_app.models import Work
from core.edition.infra.edition_django_app.models import Edition
from core.work.infra.work_django_app.serializers import (
    WorkDetailSerializer,
    WorkWriteSerializer
)
from core.cross_cutting_themes.infra.cross_cutting_themes_django_app.models import CrossCuttingTheme
from core.__seedwork.actions.work_paths import create_paths_and_links

from core.work.domain.tasks import notify_advisor_on_data_update


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
        instance = self.get_object()

        if work.verification_token is None and work.final_submission_work_date is not None:
            token = str(uuid4())
            work.verification_token = token
            work.final_submission_work_date = None
            work.status = Work.WorkStatus.PENDING
            work.save()

            accept_work_link, reject_work_link = create_paths_and_links(instance, token=token)

            notify_advisor_on_data_update.delay(
             instance.id, 
             accept_work_link=accept_work_link, 
             reject_work_link=reject_work_link
             )

        return response

        