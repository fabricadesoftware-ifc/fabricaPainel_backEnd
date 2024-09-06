from rest_framework.routers import DefaultRouter

from core.edition.infra.edition_django_app.views import EditionViewSet, EditionOpenViewSet

router = DefaultRouter()

router.register(r"edition", EditionViewSet, basename="edition")
router.register(r"edition-open", EditionOpenViewSet, basename="edition-open")
