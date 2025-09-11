from rest_framework.routers import DefaultRouter

from core.user.infra.user_django_app import views

app_name = "core.user.infra.user_django_app"

router = DefaultRouter()
router.register("users", views.UserViewSet, basename="user")
router.register("advisors", views.AdvisorViewSet, basename="advisor")
router.register("evaluators", views.EvaluatorViewSet, basename="evaluator")
router.register("classes", views.ClassViewSet, basename="class")
router.register("user_classes", views.UserClassViewSet, basename="user_class")
router.register("specialties", views.SpecialtyViewSet, basename="specialty")
router.register("certificates", views.CertificateViewSet, basename="certificate")
