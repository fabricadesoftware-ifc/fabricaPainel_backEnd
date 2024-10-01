from rest_framework.viewsets import ModelViewSet
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.throttling import UserRateThrottle
from rest_framework.response import Response
from django.db.models import Q

from core.work.infra.work_django_app.models import Team, Token
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
        sender_id = request.data.get('sender_id')
        if not team_members:
            return Response({"error": "Você deve fornecer membros para o time."}, status=status.HTTP_400_BAD_REQUEST)

        # Cria o time normalmente
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        team: Team = serializer.save()
        
        if sender_id:
            get_sender_team = Team.objects.filter(team_members__id=sender_id).filter(~Q(id=team.id))
            
            if get_sender_team:
                team.delete()
                return Response({"error": "Voce já está em um time."}, status=status.HTTP_400_BAD_REQUEST)
            sender_user = User.objects.get(id=sender_id)
            team.team_members.set([sender_user])
            team.save()

        # Gera tokens para cada membro do time
        tokens = []
        for member_id in team_members:
            try:
                member = User.objects.get(id=member_id)
                token = team.generate_token()
                sender = User.objects.get(id=sender_id)
                new_token = Token.objects.create(user=member, token=token, sender=sender)
                
                if member.id == sender_id:
                    team.accept_tokens.add(new_token)
                    continue;
                
                get_member_team = Team.objects.filter(team_members__id=member_id)
                
                if get_member_team:
                    new_token.delete()
                    team.delete()
                    return Response({"error": f"{member.name.upper()} já está em um time."}, status=status.HTTP_400_BAD_REQUEST)
                
                tokens.append(new_token)

                # if member:
                #     send_email_to_member(member, token, team.id)

            except User.DoesNotExist:
                continue
            
        for token in tokens:
            send_email_to_member(token.user, token.token, team.id)
            
        team.tokens.set(tokens)
        team.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def partial_update(self, request, *args, **kwargs):
        team: Team = self.get_object()
        action = request.data.get('action')
        token_id = request.data.get('token_id')
        user_id = request.data.get('user_id', '')
        new_members = request.data.get('new_members', [])
        sender_id = request.data.get('sender_id', '')
        
        members_token = []
        if action == 'add':
            for id in new_members:
                member = User.objects.get(id=id)
                token = team.generate_token()
                sender = User.objects.get(id=sender_id)
                new_token = Token.objects.create(user=member, token=token, sender=sender)
                team.tokens.add(new_token)
                team.save()
                members_token.append(new_token)
                
            for token in members_token:
                send_email_to_member(token.user, token.token, team.id)
                
            return Response({"message": "Usuário adicionado ao time."}, status=status.HTTP_200_OK)
        
        if action == 'remove':
            user = User.objects.get(id=user_id)
            token = team.reject_tokens.get(user=user)
            team.reject_tokens.remove(token)
            team.save()
            return Response({"message": "Usuário removido do time."}, status=status.HTTP_200_OK)
        
        if action == 'leave':
            user = User.objects.get(id=user_id)
            team.team_members.remove(user)
            token = team.accept_tokens.get(user=user)
            team.accept_tokens.remove(token)
            team.save()
            if team.team_members.count() == 0:
                team.delete()
            return Response({"message": "Usuário saiu do time."}, status=status.HTTP_200_OK)

        if not action or not token_id:
            return Response({"error": "Ação e ID do usuário com token são obrigatórios."}, status=status.HTTP_400_BAD_REQUEST)

        if action == 'accept':
            token = Token.objects.get(id=token_id)
            token_user = User.objects.get(id=token.user.id)
            
            if token in team.reject_tokens.all():
                team.reject_tokens.remove(token)
                
            if token in team.accept_tokens.all():
                return Response({"error": "Usuário já está no time."}, status=status.HTTP_400_BAD_REQUEST)
            
            team.tokens.remove(token)
            team.accept_tokens.add(token)
            team.team_members.add(token_user)
        
        elif action == 'reject':
            token = Token.objects.get(id=token_id)
            
            if token in team.accept_tokens.all():
                team.accept_tokens.remove(token)
                
            if token in team.reject_tokens.all():
                return Response({"error": "Usuário nao está no time."}, status=status.HTTP_400_BAD_REQUEST)
            
            if token.user in team.team_members.all():
                team.team_members.remove(token.user)
            
            team.tokens.remove(token)
            team.reject_tokens.add(token)

        team.save()

        return Response({"message": f"Usuário {action} com sucesso."}, status=status.HTTP_200_OK)