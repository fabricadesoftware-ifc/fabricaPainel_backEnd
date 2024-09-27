from django_filters.rest_framework import (
    FilterSet,
    CharFilter,
)

from core.cross_cutting_themes.infra.cross_cutting_themes_django_app.models import CrossCuttingTheme

class CrossCuttingThemeFilter(FilterSet):
    name = CharFilter(field_name='name', lookup_expr='icontains')

    class Meta:
        model = CrossCuttingTheme
        fields = ['name']