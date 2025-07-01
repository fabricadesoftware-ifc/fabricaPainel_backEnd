from django.contrib import admin

from core.assessment.infra.assessment_django_app.models import Assessment, Assessments, StudentAssessments

admin.site.register(Assessment)
admin.site.register(Assessments)
admin.site.register(StudentAssessments)