from rest_framework.viewsets import ModelViewSet
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.throttling import UserRateThrottle
from rest_framework.response import Response
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta

from core.work.infra.work_django_app.models import Team, Token
from core.work.infra.work_django_app.serializers import TeamDetailSerializer, TeamWriteSerializer
from core.user.infra.user_django_app.models import User
from core.work.domain.tasks.send_email_student.send_email_to_member import send_email_to_member
from core.edition.infra.edition_django_app.models import Edition

from rest_framework.throttling import UserRateThrottle
from core.work.infra.work_django_app.filters import TeamFilter

from django_project.permissions import IsStudentOrReadOnly

@extend_schema(tags=['team'])
class TeamViewSet(ModelViewSet):
    queryset = Team.objects.all()
    serializer_class = TeamDetailSerializer
    throttle_classes = [UserRateThrottle]
    filterset_class = TeamFilter
    permission_classes = [IsStudentOrReadOnly]

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return TeamDetailSerializer
        return TeamWriteSerializer
    http_method_names = ['get', 'post', 'patch', 'delete']


    def create(self, request, *args, **kwargs):
        team_members = request.data.get('team_members', [])
        sender_id = request.data.get('sender_id')
        if not team_members:
            return Response({"error": "Você deve fornecer membros para o equipe."}, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        team: Team = serializer.save()

        if sender_id:
            get_sender_team = Team.objects.filter(team_members__id=sender_id).filter(~Q(id=team.id)).exclude(work__status=4)

            if get_sender_team:
                team.delete()
                return Response({"error": "Voce já está em um time."}, status=status.HTTP_400_BAD_REQUEST)

            for member_id in team_members:
                try:
                    member = User.objects.get(id=member_id)
                    get_member_team = Team.objects.filter(team_members__id=member_id).filter(~Q(id=team.id)).exclude(work__status=4)

                    if get_member_team:
                        team.delete()
                        return Response({"error": f"{member.name.upper()} já está em um time."}, status=status.HTTP_400_BAD_REQUEST)
                except User.DoesNotExist:
                    continue

            sender_user = User.objects.get(id=sender_id)
            team.team_members.set([sender_user])
            team.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def partial_update(self, request, *args, **kwargs):
        team: Team = self.get_object()

        if hasattr(team, 'work') and team.work.status == 4:  # REJECTED
            return Response(
                {"error": "Este time está associado a um trabalho rejeitado e não pode ser alterado."},
                status=status.HTTP_400_BAD_REQUEST
            )

        action = request.data.get('action')
        user_id = request.data.get('user_id', '')
        new_members = request.data.get('new_members', [])
        if action == 'add':
            for id in new_members:
                member = User.objects.get(id=id)
                team_user = Team.objects.filter(team_members__id=id).filter(~Q(id=team.id)).exclude(work__status=4)
                if team_user:
                    return Response({"error": f"{member.name} já está em um time."}, status=status.HTTP_400_BAD_REQUEST)
                team.team_members.add(member)

            return Response({"message": "Usuário adicionado ao time."}, status=status.HTTP_200_OK)

        if action == 'remove':
            user = User.objects.get(id=user_id)
            team.team_members.remove(user)
            return Response({"message": "Usuário removido do time."}, status=status.HTTP_200_OK)

        if action == 'leave':
            user = User.objects.get(id=user_id)
            team.team_members.remove(user)
            if team.team_members.count() == 0:
                team.delete()
            return Response({"message": "Usuário saiu do time."}, status=status.HTTP_200_OK)

        if not action:
            return Response({"error": "Ação é obrigatória."}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"message": f"Usuário {action} com sucesso."}, status=status.HTTP_200_OK)
