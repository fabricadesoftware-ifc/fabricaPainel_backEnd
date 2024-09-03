from rest_framework.routers import DefaultRouter

from core.edition.router import router as edition_router
from core.field.router import router as field_router
from core.assessment.router import router as assessment_router
from core.work.router import router as work_router
from core.uploader.router import router as uploader_router
from core.user.router import router as user_router

router = DefaultRouter()
router.registry.extend(edition_router.registry)
router.registry.extend(field_router.registry)
router.registry.extend(assessment_router.registry)
router.registry.extend(work_router.registry)
router.registry.extend(uploader_router.registry)
router.registry.extend(user_router.registry)

