
from django_filters.rest_framework import (
    FilterSet,
    NumberFilter
)

from core.edition.infra.edition_django_app.models import Edition

class EditionFilter(FilterSet):
    year = NumberFilter(field_name='year')

    class Meta:
        model = Edition
        fields = ['year']