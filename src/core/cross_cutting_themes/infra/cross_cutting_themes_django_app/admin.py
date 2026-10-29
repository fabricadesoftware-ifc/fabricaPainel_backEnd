from django.contrib import admin

from .models import CrossCuttingTheme


@admin.register(CrossCuttingTheme)
class CrossCuttingThemeAdmin(admin.ModelAdmin):
    list_display = ("name", "description")
    search_fields = ("name", "description", "advisor__name", "advisor__email")
    search_help_text = "Pesquise por: nome, descrição ou orientador (nome/e-mail)."
    autocomplete_fields = ["advisor"]
