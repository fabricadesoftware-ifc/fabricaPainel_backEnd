from django.contrib import admin
from .models import Edition, EvaluationDailyWindow


class EvaluationDailyWindowInline(admin.TabularInline):
    model = EvaluationDailyWindow
    extra = 1


@admin.register(Edition)
class EditionAdmin(admin.ModelAdmin):
    inlines = [EvaluationDailyWindowInline]


@admin.register(EvaluationDailyWindow)
class EvaluationDailyWindowAdmin(admin.ModelAdmin):
    list_display = ("edition", "date", "opens_at", "closes_at")
    list_filter = ("edition",)
    ordering = ("edition", "date")