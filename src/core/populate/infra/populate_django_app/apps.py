from django.apps import AppConfig


class PopulateDjangoAppConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "core.populate.infra.populate_django_app"