from rest_framework.routers import DefaultRouter

from core.field.infra.field_django_app.views import FieldViewSet

router = DefaultRouter()

router.register(r"field", FieldViewSet)
