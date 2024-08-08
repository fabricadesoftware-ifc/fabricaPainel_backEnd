from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.utils.translation import gettext_lazy as _
from rest_framework import status
from core.user.models import User as Usuario
from core.user.use_case.read_json import read_json

@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def student_register(request) -> Response:
    email: str = request.data.get("email")
    password: str = request.data.get("password")
    registration: str = request.data.get("registration")

    json_path: str  = "/home/lucas/school/projects-fabrica/fabricaPainel_backEnd/src/core/user/json_list/student_list.json"

    if not email or not registration:
        return Response({"message": _("Email and matricula are required.")}, status=status.HTTP_400_BAD_REQUEST)
    
    if Usuario.objects.filter(email=email).exists():
        return Response({"message": _("This user already exist.")}, status=status.HTTP_400_BAD_REQUEST)

    if read_json(json_path, registration) is None:
        return Response({"message": _("Invalid registration.")}, status=status.HTTP_400_BAD_REQUEST)

    usuario = Usuario.objects.create(email=email, registration=registration)
    usuario.set_password(password)
    usuario.UserType = Usuario.UserType.STUDENT
    usuario.save()

    return Response({"message": _("Student user created successfully")}, status=status.HTTP_201_CREATED)
