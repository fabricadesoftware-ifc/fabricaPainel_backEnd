from django.contrib import admin
from core.work.infra.work_django_app.models import Work, Ods, Team

# Register your models here.
admin.site.register(Work)
admin.site.register(Ods)
admin.site.register(Team)
