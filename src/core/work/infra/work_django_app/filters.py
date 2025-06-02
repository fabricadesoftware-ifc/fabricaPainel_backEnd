from django_filters.rest_framework import FilterSet, CharFilter, BaseInFilter, ModelChoiceFilter
from unidecode import unidecode
from core.work.infra.work_django_app.models import (
    Work,
    Ods,
    Team
)

class TeamFilter(FilterSet):
    team_member_name = CharFilter(
        field_name="team_members__name", lookup_expr="icontains"
    )
    team_member_id = CharFilter(
        field_name="team_members__id", lookup_expr="exact"
    )
    
    class Meta:
        model = Team
        fields = ["team_members"]

class WorkFilter(FilterSet):
    title = CharFilter(field_name="title", lookup_expr="icontains")
    field = CharFilter(field_name="field__name", lookup_expr="icontains")
    theme = CharFilter(method="filter_theme")
    status = BaseInFilter(field_name="status", lookup_expr="in")
    advisor_id = CharFilter(field_name="advisor__id", lookup_expr="exact")
    evaluator_id = CharFilter(field_name="evaluator__id", lookup_expr="exact")
    
    # Filtros para colaboradores
    collaborator_id = CharFilter(field_name="work_collaborator__collaborator__id", lookup_expr="exact")
    collaborator_name = CharFilter(field_name="work_collaborator__collaborator__name", lookup_expr="icontains")
    collaborator_email = CharFilter(field_name="work_collaborator__collaborator__email", lookup_expr="icontains")
    collaborator_status = BaseInFilter(field_name="work_collaborator__status", lookup_expr="in")
    
    team_member_id = CharFilter(
        field_name="team__team_members__id", lookup_expr="exact"
    )

    team_member_name = CharFilter(
        field_name="team__team_members__name", lookup_expr="icontains"
    )
    team_member_email = CharFilter(
        field_name="team__team_members__email", lookup_expr="icontains"
    )
    team_member_registration = CharFilter(
        field_name="team__team_members__registration", lookup_expr="icontains"
    )

    def filter_theme(self, queryset, name, value):
        normalized_value = unidecode(value).lower()

        matching_ids = [
            work.id
            for work in queryset
            if normalized_value in unidecode(work.cross_cutting_theme.name).lower()
        ]

        return queryset.filter(id__in=matching_ids)

    class Meta:
        model = Work
        fields = ["title", "field", "theme", "status", "team", "collaborator_id", "collaborator_status"]


class OdsFilter(FilterSet):
    name = CharFilter(field_name="name", lookup_expr="icontains")

    class Meta:
        model = Ods
        fields = ["name"]
