from rest_framework.routers import DefaultRouter

from core.user import views

app_name = "core.user"

router = DefaultRouter()
router.register("users", views.UserViewSet)
