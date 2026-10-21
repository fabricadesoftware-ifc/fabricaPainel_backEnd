from typing import Any, Dict, Optional
from datetime import timedelta

from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes, permission_classes, throttle_classes
from rest_framework.request import Request
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema
from rest_framework.throttling import AnonRateThrottle

from core.user.infra.user_django_app.models import User
from core.user.infra.user_django_app.utils.normalize_input import normalize_reset_token
from django_project.settings import TOKEN_EXPIRATION_SECONDS


@extend_schema(tags=["forget_password"])
@api_view(["POST"])
@throttle_classes([AnonRateThrottle])
@authentication_classes([])
@permission_classes([])
def reset_password(request: Request, *args: Any, **kwargs: Dict[str, Any]) -> Response:
    new_password: Optional[str] = request.data.get("new_password")
    token: Optional[str] = normalize_reset_token(request.data.get("token"))

    if not new_password or not token:
        return Response(
            {"message": "Senha ou token nao fornecidos."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        user: User = User.objects.get(password_reset_token=token)
    except User.DoesNotExist:
        return Response(
            {"message": "Token invalido ou expirado."},
            status=status.HTTP_404_NOT_FOUND,
        )

    if not user.password_reset_token_created:
        user.password_reset_token = None
        user.save(update_fields=["password_reset_token"])
        return Response(
            {"message": "Token invalido ou expirado."},
            status=status.HTTP_404_NOT_FOUND,
        )

    token_expiration = user.password_reset_token_created + timedelta(
        seconds=TOKEN_EXPIRATION_SECONDS
    )

    if token_expiration <= timezone.now():
        user.password_reset_token = None
        user.password_reset_token_created = None
        user.save(update_fields=["password_reset_token", "password_reset_token_created"])
        return Response(
            {"message": "Token invalido ou expirado."},
            status=status.HTTP_404_NOT_FOUND,
        )

    user.set_password(new_password)
    user.password_reset_token = None
    user.password_reset_token_created = None
    user.save()

    return Response(
        {"message": "Senha alterada com sucesso."},
        status=status.HTTP_200_OK,
    )
