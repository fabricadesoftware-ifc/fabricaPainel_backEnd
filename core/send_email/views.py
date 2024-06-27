from django.http import HttpResponse
from django.core.mail import BadHeaderError, send_mail
from django.core.exceptions import ValidationError
from rest_framework import permissions, status
from rest_framework.views import APIView
from dotenv import load_dotenv

import os


load_dotenv()


class EmailAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        # Get the fields 'subject' and 'message' from the request body
        subject = request.data["subject"]
        message = request.data["message"]
        recipient_list = ["marcusviniciusgraciano04@gmail.com"]
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
