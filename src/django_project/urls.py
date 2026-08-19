from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

from rest_framework_simplejwt.views import (
    TokenRefreshView,
    TokenBlacklistView,
)
from core.user.infra.user_django_app.views import CustomTokenObtainPairView
from core.user.infra.user_django_app.views import create_certificate, verify_certificate
from core.work.infra.work_django_app.views import (
    needs_changes_work,
    CanceledWork,
    resend_invite_team,
    WorkViewSet,
    accept_advisor_work,
    reject_advisor_work,
    advisor_work_limit_status,
    accept_submission,
    reject_submission,
    accept_collaborator_work,
    reject_collaborator_work,
)
from core.user.infra.user_django_app.utils import (
    reset_password,
    forget_password,
    validate_token,
)
from core.assessment.infra.assessment_django_app.views import (
    generate_assessment_report,
)

from .router import router


urlpatterns = [
    path("api/", include(router.urls)),
    path("api/forget_password/", forget_password, name="forget_password"),
    path("api/reset_password/", reset_password, name="reset_password"),
    path(
        "api/validate_password_token/", validate_token, name="validate_password_token"
    ),
    path("admin/", admin.site.urls),
    path("api/token/", CustomTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/token/logout/", TokenBlacklistView.as_view(), name="token_logout"),
    path("api/generate-assessment-report/<str:year>/<str:class_name>/", generate_assessment_report, name="generate-assessment-report"),
    path("api/generate-assessment-report/<str:year>/", generate_assessment_report, name="generate-assessment-report-by-class"),
    path(
        "api/needs-changes-work/<str:pk>/",
        needs_changes_work,
        name="needs-changes-work",
    ),
    path("api/canceled-work/<str:pk>/", CanceledWork.as_view(), name="canceled-work"),
    #orientador
    path("api/accept-advisor-work/<str:verification_token>/", accept_advisor_work, name="accept-advisor-work"),
    path("api/reject-advisor-work/<str:verification_token>/", reject_advisor_work, name="reject-advisor-work"),
    path("api/advisor-work-limit/<str:verification_token>/", advisor_work_limit_status, name="advisor-work-limit"),
    #colaborador
    path("api/accept-collaborator-work/<str:verification_token>/", accept_collaborator_work, name="accept-collaborator-work"),
    path("api/reject-collaborator-work/<str:verification_token>/", reject_collaborator_work, name="reject-collaborator-work"),
    #submissão
    path("api/accept-submission/<str:verification_token>/", accept_submission, name="accept-submission"),
    path("api/reject-submission/<str:verification_token>/", reject_submission,  name="reject-submission"),
    
    path("api/create-certificate/<str:year>/", create_certificate, name="create-certificate"),
    path("api/verify-certificate/<str:hash_validate>/", verify_certificate, name="verify-certificate"),
    
    path('', lambda request: redirect('api/', permanent=True)),
]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    import debug_toolbar

    urlpatterns += [
        path("__debug__/", include(debug_toolbar.urls)),
    ]

if settings.DEBUG:
    urlpatterns += [
        path("api/swagger/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
        path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
        path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    ]