from rest_framework.routers import DefaultRouter

from core.edition.infra.edition_django_app.router import router as edition_router
from core.field.infra.field_django_app.router import router as field_router
from core.assessment.infra.assessment_django_app.router import router as assessment_router
from core.work.infra.work_django_app.router import router as work_router
from core.uploader.infra.uploader_django_app.router import router as uploader_router
from core.user.infra.user_django_app.router import router as user_router
from core.cross_cutting_themes.infra.cross_cutting_themes_django_app.router import router as cross_cutting_themes_router

router = DefaultRouter()
router.registry.extend(edition_router.registry)
router.registry.extend(field_router.registry)
router.registry.extend(assessment_router.registry)
router.registry.extend(work_router.registry)
router.registry.extend(uploader_router.registry)
router.registry.extend(user_router.registry)
router.registry.extend(cross_cutting_themes_router.registry)

