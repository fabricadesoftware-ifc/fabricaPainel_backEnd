from rest_framework.viewsets import ModelViewSet
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.throttling import UserRateThrottle
from rest_framework.response import Response

from core.work.infra.work_django_app.models import Team
from core.work.infra.work_django_app.serializers import TeamDetailSerializer, TeamWriteSerializer
from core.user.infra.user_django_app.models import User
from core.work.domain.tasks.send_email_student.send_email_to_member import send_email_to_member

from rest_framework.throttling import UserRateThrottle
from core.work.infra.work_django_app.filters import TeamFilter

@extend_schema(tags=['team'])
class TeamViewSet(ModelViewSet):
    queryset = Team.objects.all()
    serializer_class = TeamDetailSerializer
    throttle_classes = [UserRateThrottle]
    filterset_class = TeamFilter

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return TeamDetailSerializer
        return TeamWriteSerializer
    http_method_names = ['get', 'post', 'patch', 'delete']


    def create(self, request, *args, **kwargs):
        team_members = request.data.get('team_members', [])
        if not team_members:
            return Response({"error": "Você deve fornecer membros para o time."}, status=status.HTTP_400_BAD_REQUEST)

        # Cria o time normalmente
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        team = serializer.save()

        # Gera tokens para cada membro do time
        tokens = {}
        for member_id in team_members:
            try:
                member = User.objects.get(id=member_id)
                token = team.generate_token()
                tokens[str(member.id)] = token

                if member:
                    send_email_to_member(member, token)

            except User.DoesNotExist:
                continue
        
        team.tokens = tokens
        team.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def partial_update(self, request, *args, **kwargs):
        team = self.get_object()
        action = request.data.get('action')
        token_user_id = request.data.get('token_user_id')

        if not action or not token_user_id:
            return Response({"error": "Ação e ID do usuário com token são obrigatórios."}, status=status.HTTP_400_BAD_REQUEST)

        if action == 'accept':
            # Mover o token para 'accept_tokens'
            if str(token_user_id) in team.tokens:
                token = team.tokens.pop(str(token_user_id))
                team.accept_tokens[str(token_user_id)] = token
                team.team_members.add(token_user_id)
            else:
                return Response({"error": "Token não encontrado para o usuário."}, status=status.HTTP_404_NOT_FOUND)
        
        elif action == 'reject':
            # Mover o token para 'reject_tokens'
            if str(token_user_id) in team.tokens:
                token = team.tokens.pop(str(token_user_id))
                team.reject_tokens[str(token_user_id)] = token
            else:
                return Response({"error": "Token não encontrado para o usuário."}, status=status.HTTP_404_NOT_FOUND)

        team.save()

        return Response({"message": f"Usuário {action} com sucesso."}, status=status.HTTP_200_OK)