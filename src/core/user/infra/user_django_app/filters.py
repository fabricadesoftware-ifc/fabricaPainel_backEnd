from django_filters.rest_framework import (
    FilterSet,
    CharFilter,
    BaseInFilter,
    NumberFilter,
)
from django_project.settings import MODE
from core.user.infra.user_django_app.models import User, Evaluator
from django.db.models import Q
from django.db.models import Func
import unicodedata


def remove_accents(input_str):
    return ''.join(c for c in unicodedata.normalize('NFKD', input_str) if not unicodedata.combining(c)).lower()

class Unaccent(Func):
    function = 'unaccent'
    template='%(function)s(%(expressions)s)'
class UserFilter(FilterSet):
    name = CharFilter(method="filter_name")
    field = CharFilter(field_name="field__name", lookup_expr="icontains")
    type = BaseInFilter(field_name="user_type", lookup_expr="in")
    registration = CharFilter(field_name="registration", lookup_expr="icontains")
    
    def filter_name(self, queryset, name, value):
        if MODE == "DEVELOPMENT":
            value_normalized = remove_accents(value)
            return queryset.filter(
                name__isnull=False
            ).filter(
                pk__in=[
                    user.pk for user in queryset
                    if user.name and remove_accents(user.name).lower().find(value_normalized) != -1
                ]
            )

        return queryset.annotate(
            name_unaccent=Unaccent('name')
        ).filter(name_unaccent__icontains=value)
    
    # Opção 1: Filtro atual - busca por IDs das classes
    
    # Opção 2: Se quiser filtrar por nome da classe
    user_classes = CharFilter(field_name="user_classes__class_name__name", lookup_expr="icontains")
    
    # Opção 3: Se quiser filtrar por ano da classe
    # user_classes_year = NumberFilter(field_name="user_classes__year", lookup_expr="exact")
    
    # Opção 4: Se quiser filtrar por múltiplos anos
    # user_classes_year = BaseInFilter(field_name="user_classes__year", lookup_expr="in")

    # Filtros adicionais para facilitar buscas por classes
    class_name = CharFilter(field_name="user_classes__class_name__name", lookup_expr="icontains")
    class_year = NumberFilter(field_name="user_classes__year", lookup_expr="exact")

    search = CharFilter(method="search_filter")

    def search_filter(self, queryset, name, value):
        return queryset.filter(Q(registration__icontains=value))

    class Meta:
        model = User
        fields = ["name", "field", "registration", "user_type", "class_name", "class_year"]


class EvaluatorFilter(FilterSet):
    user_id = NumberFilter(field_name="user__id", lookup_expr="exact")

    class Meta:
        model = Evaluator
        fields = ["user"]
