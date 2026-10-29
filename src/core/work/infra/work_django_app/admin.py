from django import forms
from django.contrib import admin
from rest_framework.exceptions import ValidationError as DRFValidationError
from core.work.infra.work_django_app.models import Work, Ods, Team, WorkCollaborator
from core.work.domain.validations import validate_work_evaluator_limits

# Inline para exibir os colaboradores do trabalho no admin
class WorkCollaboratorInline(admin.TabularInline):
    model = WorkCollaborator
    extra = 1  # número de linhas extras em branco para adicionar

class WorkAdminForm(forms.ModelForm):
    class Meta:
        model = Work
        fields = "__all__"

    def clean(self):
        cleaned_data = super().clean()
        evaluators = cleaned_data.get("evaluator")
        edition = cleaned_data.get("edition")

        if evaluators and edition:
            try:
                validate_work_evaluator_limits(edition, evaluators, current_work_id=self.instance.pk)
            except DRFValidationError as exc:
                raise forms.ValidationError({"evaluator": str(exc.detail[0])})

        return cleaned_data

# Admin customizado para o modelo Work
@admin.register(Work)
class WorkAdmin(admin.ModelAdmin):
    form = WorkAdminForm
    inlines = [WorkCollaboratorInline]
    list_display = ("title", "work_kind", "advisor", "status", "advisor_status", "get_year")
    list_select_related = ("advisor", "edition")
    # Sem isso, esses campos viravam um <select> gigante com TODOS os registros
    # (todas as equipes, todos os usuários, todas as disciplinas...), que
    # estourava a tela e não dava pra pesquisar. Com autocomplete_fields vira
    # um campo de busca (Select2) que carrega os resultados sob demanda.
    autocomplete_fields = ["team", "advisor", "field", "evaluator"]
    search_fields = (
        "title",
        "advisor__name",
        "advisor__email",
        "team__team_members__name",  # nome de qualquer membro da equipe
        "=edition__year",  # busca exata por ano da edição
    )
    search_help_text = (
        "Pesquise por: título, orientador (nome/e-mail), membro da equipe ou ano da edição (exato). "
        "Exemplos: 'robótica', 'maria', '2025'"
    )
    list_filter = (
        "status",
        "advisor_status",
        "work_kind",
        "integrated_project",
        "edition__year",
        "cross_cutting_theme",
    )
    
    def get_year(self, obj):
        return obj.edition.year
    get_year.short_description = "Ano"

@admin.register(Ods)
class OdsAdmin(admin.ModelAdmin):
    search_fields = ("name",)


@admin.register(WorkCollaborator)
class WorkCollaboratorAdmin(admin.ModelAdmin):
    list_display = ("work", "collaborator", "status", "get_year")
    list_select_related = ("work", "work__edition", "collaborator")
    autocomplete_fields = ["work", "collaborator"]
    search_fields = (
        "work__title",
        "collaborator__name",
        "collaborator__email",
    )
    search_help_text = "Pesquise por: título do trabalho ou nome/e-mail do colaborador."
    list_filter = ("status", "work__edition__year")

    @admin.display(description="Ano", ordering="work__edition__year")
    def get_year(self, obj):
        return obj.work.edition.year


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    autocomplete_fields = ["team_members"]
    list_select_related = ("edition",)

    def get_queryset(self, request):
        # __str__ da equipe lista os membros: sem isso, uma query por linha.
        return super().get_queryset(request).prefetch_related("team_members")

    search_fields = (
        "team_members__name",
        "team_members__registration",
    )
    search_help_text = (
        "Pesquise por: nome do membro ou matrícula. "
        "Exemplos: 'joao', '12345'"
    )
    list_filter = ("edition__year",)