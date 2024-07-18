from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from core.fabrica_painel.views import (
    AssessmentsViewSet,
    AssessmentViewSet,
    EditionViewSet,
    FieldViewSet,
    KeywordViewSet,
    TeamViewSet,
    WorkViewSet,
)
from core.fabrica_painel.views.accept_work import accept_work
from core.uploader.router import router as uploader_router
from core.usuario.router import router as usuario_router
from core.usuario.use_case.register_validation import create_user

router = DefaultRouter()
router.register("assessment", AssessmentViewSet)
router.register("assessments", AssessmentsViewSet)
router.register("keyword", KeywordViewSet)
router.register("team", TeamViewSet)
router.register("work", WorkViewSet)
router.register("edition", EditionViewSet)
router.register("field", FieldViewSet)

urlpatterns = [
    path("api/", include(router.urls)),
    path("api/register/", create_user, name="create_user"),
    path("admin/", admin.site.urls),
    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/", include(usuario_router.urls)),
    path("api/media/", include(uploader_router.urls)),
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
    path("accept-work/<str:verification_token>/", accept_work, name="accept-work"),
]

urlpatterns += static(settings.MEDIA_ENDPOINT, document_root=settings.MEDIA_ROOT)
