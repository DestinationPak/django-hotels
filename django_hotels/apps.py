from django.apps import AppConfig


class DjangoHotelsConfig(AppConfig):
    name = "django_hotels"
    verbose_name = "Django Hotels"
    # Pinned per-app so this package's models always get BigAutoField
    # regardless of the consuming project's own DEFAULT_AUTO_FIELD.
    default_auto_field = "django.db.models.BigAutoField"
