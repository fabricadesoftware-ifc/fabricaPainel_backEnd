from django_filters.rest_framework import (
    FilterSet,
    CharFilter,
    BaseInFilter
)
from core.work.infra.work_django_app.models import Work, Ods  # Import correto do modelo Ods


class WorkFilter(FilterSet):
    title = CharFilter(field_name='title', lookup_expr='icontains')
    field = CharFilter(field_name='field__name', lookup_expr='icontains')
    theme = CharFilter(field_name='cross_cutting_theme__name', lookup_expr='icontains')
    status = BaseInFilter(field_name="status", lookup_expr='in')
    
    # Ajustando os campos de team_member
    team_member_name = CharFilter(field_name='team__team_members__name', lookup_expr='icontains')
    team_member_email = CharFilter(field_name='team__team_members__email', lookup_expr='icontains')
    team_member_registration = CharFilter(field_name='team__team_members__registration', lookup_expr='icontains')

    class Meta:
        model = Work
        fields = ['title', 'field', 'theme', 'status']  


class OdsFilter(FilterSet):
    name = CharFilter(field_name='name', lookup_expr='icontains')

    class Meta:
        model = Ods  
        fields = ['name']
