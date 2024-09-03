from rest_framework.routers import DefaultRouter

from core.field.views import FieldViewSet

router = DefaultRouter()

router.register(r"field", FieldViewSet)
