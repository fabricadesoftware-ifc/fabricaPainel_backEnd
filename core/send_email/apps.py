from django.apps import AppConfig


class SendEmailConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core.send_email'

    def ready(self) -> None:
        import core.send_email.signals
