from rest_framework.routers import DefaultRouter

from core.work.views import WorkViewSet, KeywordViewSet, TeamViewSet, OdsViewSet


router = DefaultRouter()

router.register(r"work", WorkViewSet)
router.register(r"keyword", KeywordViewSet)
router.register(r"team", TeamViewSet)
router.register(r"ods", OdsViewSet)