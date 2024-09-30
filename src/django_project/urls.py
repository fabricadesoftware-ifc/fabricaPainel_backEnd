from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

from rest_framework_simplejwt.views import (
    TokenRefreshView,
)
from core.user.infra.user_django_app.views import CustomTokenObtainPairView
from core.work.infra.work_django_app.views import approve_work, needs_changes_work, CanceledWork
from core.user.infra.user_django_app.utils import reset_password, forget_password, validate_token

from .router import router


urlpatterns = [
    path("api/", include(router.urls)),
    path("api/forget_password/", forget_password, name="forget_password"),
    path("api/reset_password/", reset_password, name="reset_password"),
    path("api/validate_password_token/", validate_token, name="validate_password_token"),
    path("admin/", admin.site.urls),
    path("api/token/", CustomTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/swagger/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path(
        "api/redoc/",
        SpectacularRedocView.as_view(url_name="schema"),
        name="redoc",
    ),
    path("api/accept-work/<str:verification_token>/", approve_work, name="accept-work"),
    path("api/needs-changes-work/<str:pk>/", needs_changes_work, name="needs-changes-work"),
    path("api/canceled-work/<str:pk>/", CanceledWork.as_view(), name="canceled-work"),
]

urlpatterns += static(settings.MEDIA_ENDPOINT, document_root=settings.MEDIA_ROOT)
