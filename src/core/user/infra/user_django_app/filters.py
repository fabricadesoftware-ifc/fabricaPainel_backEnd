from django_filters.rest_framework import (
    FilterSet,
    CharFilter,
    BaseInFilter,
    NumberFilter,
)
from core.user.infra.user_django_app.models import User, Evaluator
from django.db.models import Q


class UserFilter(FilterSet):
    name = CharFilter(field_name="name", lookup_expr="icontains")
    field = CharFilter(field_name="field__name", lookup_expr="icontains")
    type = BaseInFilter(field_name="user_type", lookup_expr="in")
    registration = CharFilter(field_name="registration", lookup_expr="icontains")

    search = CharFilter(method="search_filter")

    def search_filter(self, queryset, name, value):
        return queryset.filter(Q(registration__icontains=value))

    class Meta:
        model = User
        fields = ["name", "field", "registration", "user_type"]


class EvaluatorFilter(FilterSet):
    user_id = NumberFilter(field_name="user__id", lookup_expr="exact")

    class Meta:
        model = Evaluator
        fields = ["user"]
