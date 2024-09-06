from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from django_project.settings import EMAIL_HOST_USER

from tasks import send_work_cancel_email_to_advisor
from tasks import send_work_cancel_email_to_student
from core.work.infra.work_django_app.models import Work


class CanceledWork(APIView):
    def patch(args, **kwargs) -> Response:
        try:
            work = Work.objects.get(pk=kwargs["pk"])
        except Work.DoesNotExist:
            return Response(
                {"error": "Trabalho não encontrado."},
                status=status.HTTP_404_NOT_FOUND,
            )
        work_id = work.id

        from_email = EMAIL_HOST_USER
        try:
            send_work_cancel_email_to_advisor.delay(work_id, from_email)
            send_work_cancel_email_to_student.delay(work_id, from_email)
        except:
            return Response(
                    {"error": "Erro ao enviar os emails."},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
            
        return Response(
                {"message": "O trabalho foi cancelado com sucesso."},
                status=status.HTTP_200_OK,
            )
       