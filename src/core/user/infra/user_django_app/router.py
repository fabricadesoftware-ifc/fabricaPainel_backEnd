from rest_framework.routers import DefaultRouter

from core.user.infra.user_django_app import views

app_name = "core.user.infra.user_django_app"

router = DefaultRouter()
router.register("users", views.UserViewSet)
