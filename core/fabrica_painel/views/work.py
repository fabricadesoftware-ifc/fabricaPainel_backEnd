from rest_framework.viewsets import ModelViewSet
from drf_spectacular.utils import extend_schema
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from asgiref.sync import async_to_sync
from core.fabrica_painel.use_case.send_work_email_to_student import send_work_email_to_student


from core.fabrica_painel.models.work import Work
from core.fabrica_painel.serializers.work import (
    WorkDetailSerializer,
    WorkWriteSerializer
)

import os 
from dotenv import load_dotenv

load_dotenv()

@extend_schema(tags=["work"])
class WorkViewSet(ModelViewSet):
    queryset = Work.objects.all()
    serializer_class = WorkDetailSerializer

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return WorkDetailSerializer
        return WorkWriteSerializer
    http_method_names = ["get", "post", "patch", "delete"]


@api_view(["GET"])
def accept_work(request, verification_token) -> Response:
    try:
        work = Work.objects.get(verification_token=verification_token)
    except Work.DoesNotExist:
        return Response(
            {"error": "Trabalho não encontrado."},
            status=status.HTTP_404_NOT_FOUND,
        )

    work.final_submission_work_date = timezone.now()
    work.verification_token = None
    work.save()

    email_student_recipient_list = [work.team]
    from_email = os.getenv("EMAIL_HOST_USER")

    if work.final_submission_work_date is not None:
        async_to_sync(send_work_email_to_student)(from_email, email_student_recipient_list)


    return Response(
        {"message": "Trabalho aceito."},
        status=status.HTTP_200_OK,
    )
