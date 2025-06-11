from django.contrib import admin
from core.work.infra.work_django_app.models import Work, Ods, Team, WorkCollaborator

# Inline para exibir os colaboradores do trabalho no admin
class WorkCollaboratorInline(admin.TabularInline):
    model = WorkCollaborator
    extra = 1  # número de linhas extras em branco para adicionar

# Admin customizado para o modelo Work
@admin.register(Work)
class WorkAdmin(admin.ModelAdmin):
    inlines = [WorkCollaboratorInline]
    list_display = ("title", "advisor", "status")  # ajuste conforme seu modelo

# Registro padrão dos outros modelos
admin.site.register(Ods)
admin.site.register(Team)