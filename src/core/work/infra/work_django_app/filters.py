from django_filters.rest_framework import (
    FilterSet,
    CharFilter,
    BaseInFilter
)
from core.work.infra.work_django_app.models import Work


class WorkFilter(FilterSet):
    title = CharFilter(field_name='title', lookup_expr='icontains')
    field = CharFilter(field_name='field', lookup_expr='icontains')
    theme = CharFilter(field_name='cross_cutting_theme', lookup_expr='icontains')
    status = BaseInFilter(field_name="status__id", lookup_expr='in')
    team_member_name = CharFilter(field_name='team_name', lookup_expr='icontains')
    team_member_email = CharFilter(field_name='team_email', lookup_expr='icontains')
    team_member_registration = CharFilter(field_name='team_registration', lookup_expr='icontains')

    class Meta:
        model = Work
        fields = ['title', 'type', 'field', 'theme', 'status']


class OdsFilter(FilterSet):
    name = CharFilter(field_name='name', lookup_expr='icontains')

    class Meta:
        model = Work
        fields = ['name']