import secrets
from django.utils import timezone

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, authentication_classes, throttle_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from drf_spectacular.utils import extend_schema
from rest_framework.throttling import AnonRateThrottle

from core.user.infra.user_django_app.models import User
from core.user.infra.user_django_app.utils.normalize_input import find_user_by_email, normalize_email_input
from core.work.domain.tasks.send_forget_password_email import send_forget_password_email


@extend_schema(tags=["forget_password"])
@api_view(['POST'])
@throttle_classes([AnonRateThrottle])
@permission_classes([AllowAny])
@authentication_classes([])
def forget_password(request):
    email = normalize_email_input(request.data.get('email'))
    try:
        user = find_user_by_email(User, email)
        if user is None:
            raise User.DoesNotExist

        # Gera novo token
        desired_length = 8
        token_size = (desired_length + 1) // 2
        token = secrets.token_hex(token_size)

        # Salva token e timestamp (sobrescreve o antigo se existir)
        user.password_reset_token = token
        user.password_reset_token_created = timezone.now()
        user.save()  # Save completo - update_fields causava problema em produção

        send_forget_password_email.delay(user.email, token)

        return Response(status=status.HTTP_200_OK, data={"message": "Email enviado com sucesso."})

    except User.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND, data={"message": "Usuário não encontrado."})


