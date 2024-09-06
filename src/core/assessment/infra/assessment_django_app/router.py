from rest_framework.routers import DefaultRouter

from core.assessment.infra.assessment_django_app.views import AssessmentViewSet
from core.assessment.infra.assessment_django_app.views import AssessmentsViewSet

router = DefaultRouter()

router.register(r"assessment", AssessmentViewSet)
router.register(r"assessments", AssessmentsViewSet)