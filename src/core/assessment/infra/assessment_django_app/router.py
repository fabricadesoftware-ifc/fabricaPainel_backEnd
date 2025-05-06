from rest_framework.routers import DefaultRouter

from core.assessment.infra.assessment_django_app.views import AssessmentViewSet, StudentAssessmentsViewSet


router = DefaultRouter()

router.register(r"assessment", AssessmentViewSet)
router.register(r"student-assessments", StudentAssessmentsViewSet, basename='student-assessment')