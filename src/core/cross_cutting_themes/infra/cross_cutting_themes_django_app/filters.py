from django_filters.rest_framework import (
    FilterSet,
    CharFilter,
)

from core.cross_cutting_themes.infra.cross_cutting_themes_django_app.models import CrossCuttingTheme

class CrossCuttingThemeFilter(FilterSet):
    name = CharFilter(field_name='name', lookup_expr='icontains')
    advisor_id = CharFilter(field_name='advisor', lookup_expr='exact')

    class Meta:
        model = CrossCuttingTheme
        fields = ['name', 'advisor']