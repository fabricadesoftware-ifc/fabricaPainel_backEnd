from django.core.exceptions import ValidationError
from django.core.mail import BadHeaderError, send_mail
from django.http import HttpResponse
from rest_framework import status
from rest_framework.views import APIView
from dotenv import load_dotenv

import os

load_dotenv()


class EmailAPIView(APIView):
    def post(self, request, *args, **kwargs):
        subject = request.POST.get("subject", "Nome do email")
        message = request.POST.get("message", "Conteúdo do email")
        recipient_list = []
        from_email = os.getenv("EMAIL_HOST_USER")

        try:
            send_mail(
                subject,
                message,
                recipient_list=recipient_list,
                from_email=from_email,
            )

        except BadHeaderError:
            return HttpResponse("Invalid header found.")
        except ValidationError as e:
            return HttpResponse(str(e))
        return HttpResponse({"Email enviado com sucesso"}, status=status.HTTP_200_OK)
