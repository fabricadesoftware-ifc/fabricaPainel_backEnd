from django.contrib import admin

from core.field.infra.field_django_app.models import Field


@admin.register(Field)
class FieldAdmin(admin.ModelAdmin):
    list_display = ("name",)
    # necessário para o WorkAdmin poder usar "field" em autocomplete_fields
    search_fields = ["name"]
