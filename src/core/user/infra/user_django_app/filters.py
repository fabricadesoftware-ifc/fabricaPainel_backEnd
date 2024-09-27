from django_filters.rest_framework import (
    FilterSet,
    CharFilter,
    BaseInFilter

)
from core.user.infra.user_django_app.models import User


class UserFilter(FilterSet):
    name = CharFilter(field_name='name', lookup_expr='icontains')
    field = CharFilter(field_name='field', lookup_expr='icontains')
    theme = CharFilter(field_name='cross_cutting_theme__name', lookup_expr='icontains')
    type = BaseInFilter(field_name="user_type__id", lookup_expr='in')
    registration = CharFilter(field_name='registration', lookup_expr='icontains')

    class Meta:
        model = User
        fields = ['name', 'type', 'field', 'registration']