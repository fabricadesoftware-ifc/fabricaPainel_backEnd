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
    TokenObtainPairView,
    TokenRefreshView,
)
from core.work.infra.work_django_app.views import approve_work, reject_work, CanceledWork
from core.user.infra.user_django_app.utils import reset_password, forget_password
from .router import router


urlpatterns = [
    path("api/", include(router.urls)),
    path("api/forget_password/", forget_password, name="forget_password"),
    path("api/reset_password/", reset_password, name="reset_password"),
    path("admin/", admin.site.urls),
    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
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
    path("accept-work/<str:verification_token>/", approve_work, name="approve-work"),
    path("reject-work/<str:pk>/", reject_work, name="reject-work"),
    path("canceled-work/<str:pk>/", CanceledWork.as_view(), name="canceled-work"),
]

urlpatterns += static(settings.MEDIA_ENDPOINT, document_root=settings.MEDIA_ROOT)
