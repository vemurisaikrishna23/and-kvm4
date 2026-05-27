from django.apps import AppConfig


class IotPanelConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'IoT_Panel'

    def ready(self):
        import IoT_Panel.spectacular_hooks  # noqa: F401 — registers the JWT auth extension
        from IoT_Panel.schema import apply_all_annotations
        apply_all_annotations()
