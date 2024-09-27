
from django_filters.rest_framework import (
    FilterSet,
    DateFilter,
)

from core.edition.infra.edition_django_app.models import Edition

class EditionFilter(FilterSet):
    date = DateFilter()

    class Meta:
        model = Edition
        fields = ['number', 'date']