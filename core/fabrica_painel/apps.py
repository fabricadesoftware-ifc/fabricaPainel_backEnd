from django.apps import AppConfig


class FabricaPainelConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core.fabrica_painel'

    def ready(self) -> None:
        import core.fabrica_painel.signals
        import core.fabrica_painel.use_case

