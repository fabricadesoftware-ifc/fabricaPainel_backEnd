from rest_framework.viewsets import ModelViewSet
from drf_spectacular.utils import extend_schema

from core.fabrica_painel.models.team import Team
from core.fabrica_painel.serializers.team import (
    TeamDetailSerializer,
    TeamWriteSerializer
)


@extend_schema(tags=['team'])
class TeamViewSet(ModelViewSet):
    queryset = Team.objects.all()
    serializer_class = TeamDetailSerializer

    def get_serializer_class(self):
        if self.action in ['list', 'retrive']:
            return TeamDetailSerializer
        return TeamWriteSerializer
    http_method_names = ['get', 'post', 'patch', 'delete']
