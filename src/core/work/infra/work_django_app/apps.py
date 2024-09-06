from django.apps import AppConfig


class WorkConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core.work.infra.work_django_app'

    def ready(self) -> None:
        import core.work.infra.work_django_app.signal