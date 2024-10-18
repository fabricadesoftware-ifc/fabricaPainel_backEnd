from rest_framework.decorators import api_view
from core.__seedwork.domain.tasks.assign_work_to_advisor import assign_work_to_advisor
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import permission_classes, authentication_classes
from rest_framework.permissions import AllowAny

@api_view(['GET'])
@permission_classes([AllowAny])
@authentication_classes([])
def assign_work(request, *args, **kwargs):
    try:
        assign_work_to_advisor.delay()
        
        return Response(
                {"message": "Orientadores adicionados aos trabalhos com sucesso"},
                status=status.HTTP_200_OK,
            )
    except:
        return Response(
                {"message": "Erro ao adicionar orientadores"},
                status=status.HTTP_400_BAD_REQUEST,
            )