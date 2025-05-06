from django_filters.rest_framework import (
    FilterSet,
    CharFilter
)
from core.field.infra.field_django_app.models import Field


class FieldFilter(FilterSet):
    name = CharFilter(field_name='name', lookup_expr='icontains')

    class Meta:
        model = Field
        fields = ['name']