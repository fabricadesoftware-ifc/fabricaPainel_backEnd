from django.contrib import admin

from core.assessment.infra.assessment_django_app.models import Assessment, Assessments, StudentAssessments


@admin.register(Assessment)
class AssessmentAdmin(admin.ModelAdmin):
    list_display = ("work", "evaluator", "grade", "date_time", "get_year")
    list_select_related = ("work", "work__edition", "evaluator", "evaluator__user")
    autocomplete_fields = ["work", "evaluator"]
    search_fields = (
        "work__title",
        "evaluator__user__name",
        "evaluator__user__email",
        "committee_feedback",
    )
    search_help_text = (
        "Pesquise por: título do trabalho, nome/e-mail do avaliador ou parecer da banca."
    )
    list_filter = ("work__edition__year", "work__work_kind", "date_time")
    date_hierarchy = "date_time"
    ordering = ("-date_time",)

    @admin.display(description="Ano", ordering="work__edition__year")
    def get_year(self, obj):
        return obj.work.edition.year


@admin.register(Assessments)
class AssessmentsAdmin(admin.ModelAdmin):
    list_display = ("work", "evaluator", "get_year")
    list_select_related = ("work", "work__edition", "evaluator", "evaluator__user")
    autocomplete_fields = ["work", "evaluator"]
    search_fields = (
        "work__title",
        "evaluator__user__name",
        "evaluator__user__email",
    )
    search_help_text = "Pesquise por: título do trabalho ou nome/e-mail do avaliador."
    list_filter = ("work__edition__year", "work__work_kind")

    @admin.display(description="Ano", ordering="work__edition__year")
    def get_year(self, obj):
        return obj.work.edition.year


@admin.register(StudentAssessments)
class StudentAssessmentsAdmin(admin.ModelAdmin):
    list_display = ("student", "work", "grade", "date_time", "get_year")
    list_select_related = ("student", "work", "work__edition")
    autocomplete_fields = ["work", "student"]
    search_fields = (
        "student__name",
        "student__email",
        "=student__registration",
        "work__title",
    )
    search_help_text = (
        "Pesquise por: nome, e-mail ou matrícula (exata) do aluno, ou título do trabalho."
    )
    list_filter = ("work__edition__year", "work__work_kind", "date_time")
    date_hierarchy = "date_time"
    ordering = ("-date_time",)

    @admin.display(description="Ano", ordering="work__edition__year")
    def get_year(self, obj):
        return obj.work.edition.year
