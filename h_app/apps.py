from django.apps import AppConfig


class HAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'h_app'

    def ready(self):
        # Register signals
        import h_app.signals
