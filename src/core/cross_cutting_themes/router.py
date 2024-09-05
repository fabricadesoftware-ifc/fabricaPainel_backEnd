from rest_framework.routers import DefaultRouter

from core.cross_cutting_themes.views import CrossCuttingThemeViewSet

router = DefaultRouter()

router.register(r"cross_cutting_theme", CrossCuttingThemeViewSet)
