from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.utils.translation import gettext_lazy as _
from rest_framework import status
from core.usuario.models import Usuario
from core.usuario.use_case.read_pdf_in_colums import is_value_in_pdf

@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def create_user(request):
    email = request.data.get("email")
    password = request.data.get("password")
    registration = request.data.get("matricula")

    file_path = "core/usuario/pdf_files/planilha teste dois - Página1.pdf"

    if not email or not registration:
        return Response({"message": _("Email and matricula are required.")}, status=status.HTTP_400_BAD_REQUEST)

    if not is_value_in_pdf(file_path, registration):
        return Response({"message": _("Invalid registration.")}, status=status.HTTP_400_BAD_REQUEST)

    usuario = Usuario.objects.create(email=email, registration=registration)
    usuario.set_password(password)
    usuario.save()
    return Response({"message": _("User created successfully")}, status=status.HTTP_201_CREATED)
