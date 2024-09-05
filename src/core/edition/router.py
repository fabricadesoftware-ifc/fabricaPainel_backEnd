from rest_framework.routers import DefaultRouter

from core.edition.views import EditionViewSet

router = DefaultRouter()

router.register(r"edition", EditionViewSet, basename="edition")
