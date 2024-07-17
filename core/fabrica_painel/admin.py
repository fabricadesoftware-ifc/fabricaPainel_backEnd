from django.contrib import admin
from core.fabrica_painel.models.assessment import Assessment
from core.fabrica_painel.models.assessments import Assessments
from core.fabrica_painel.models.keyword import Keyword
from core.fabrica_painel.models.work import Work
from core.fabrica_painel.models.field import Field
from core.fabrica_painel.models.edition import Edition
from core.fabrica_painel.models.team import Team
from core.fabrica_painel.models.ods import SustainableGoals

# Register your models here.

admin.site.register(Assessment)
admin.site.register(Assessments)
admin.site.register(Keyword)
admin.site.register(Work)
admin.site.register(Field)
admin.site.register(Edition)
admin.site.register(Team)
admin.site.register(SustainableGoals)