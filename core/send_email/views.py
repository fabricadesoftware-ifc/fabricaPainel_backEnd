from django.core.mail import BadHeaderError, send_mail
from rest_framework import status
from rest_framework.views import APIView
from django_project.settings import EMAIL_HOST_USER
from rest_framework.decorators import authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


@authentication_classes([])
@permission_classes([AllowAny])
class EmailAPIView(APIView):
    def post(self, request, *args, **kwargs):
        # Get the fields 'subject' and 'message' from the request body
        subject = request.data.get("subject", "titulo do email")
        message = request.data.get("message", "mensagem boladona" )
        recipient_list = ["marcusviniciusgraciano04@gmail.com", "lucasantonete@hotmail.com"]
        from_email = EMAIL_HOST_USER
        
        try:
            send_mail(
                subject, 
                message,
                from_email,
                recipient_list,
                fail_silently=False
            )

            return Response({'success': True, 'message': 'Email sent successfully.'}, status=status.HTTP_200_OK)
        except BadHeaderError:
            return Response({'success': False, 'error': 'erro'}, status=status.HTTP_400_BAD_REQUEST)