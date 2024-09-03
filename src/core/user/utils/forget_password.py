from rest_framework import status 
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from tasks.send_forget_password_email import send_forget_password_email
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from core.user.models import User
import datetime
import secrets
import pytz


@api_view(['POST'])
@permission_classes([AllowAny])
@authentication_classes([])
def forget_password(request):
    email = request.data.get('email')
    try:
        user = User.objects.get(email=email)

        if (user.password_reset_token_created is not None):
            user.password_reset_token = None

        desired_length = 8 
        token_size = (desired_length + 1) // 2
        token = secrets.token_hex(token_size)
        user.password_reset_token = token
        user.save()
        user.password_reset_token_created = pytz.utc.localize(datetime.datetime.now())
        user.save()

        send_forget_password_email.delay(email, token)

        return Response(status=status.HTTP_200_OK, data={"message": "Email enviado com sucesso."})
    
    except User.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND, data={"message": "Usuário não encontrado."})
        
    
