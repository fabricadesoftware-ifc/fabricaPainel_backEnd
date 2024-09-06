import pytz
from typing import Any, Dict, Optional
from datetime import datetime, timedelta

from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.request import Request
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema

from core.user.infra.user_django_app.models import User
from django_project.settings import TOKEN_EXPIRATION_SECONDS

extend_schema(tags=["forget_password"])
@api_view(["POST"])
@authentication_classes([])
@permission_classes([])
def reset_password(request: Request, *args: Any, **kwargs: Dict[str, Any]) -> Response:
    new_password: Optional[str] = request.data.get("new_password")
    token: Optional[str] = request.data.get("token")

    if not new_password or not token:
        return Response(
            {"message": "Senha ou token não fornecidos."},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        user: User = User.objects.get(password_reset_token=token)
    except User.DoesNotExist:
        return Response(
            {"message": "Token inválido ou esgotado."},
            status=status.HTTP_404_NOT_FOUND
        )

    if user.password_reset_token_created:
        token_expiration = user.password_reset_token_created + timedelta(seconds=TOKEN_EXPIRATION_SECONDS)

        if token_expiration > datetime.now(pytz.utc):
            user.password_reset_token = None
            user.password_reset_token_created = None
            user.save()
            return Response(
                {"message": "Token inválido ou esgotado penis."},
                status=status.HTTP_404_NOT_FOUND
            )
    user.set_password(new_password)
    user.password_reset_token = None
    user.password_reset_token_created = None
    user.save()
    
    return Response(
        {"message": "Senha alterada com sucesso."},
        status=status.HTTP_200_OK
    )
