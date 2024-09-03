from rest_framework.routers import DefaultRouter

from core.assessment.views import AssessmentViewSet
from core.assessment.views import AssessmentsViewSet

router = DefaultRouter()

router.register(r"assessment", AssessmentViewSet)
router.register(r"assessments", AssessmentsViewSet)