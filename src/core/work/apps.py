from django.apps import AppConfig


class WorkConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core.work'

    def ready(self) -> None:
        import core.work.signal