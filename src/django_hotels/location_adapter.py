"""
Adapter for reading Location fields, so callers work the same way
whether django_hotels.Location or a swapped-in model backs the FK
(DJANGO_HOTELS_LOCATION_MODEL).
"""

from django.conf import settings
from django.utils.module_loading import import_string

DEFAULT_LOCATION_ADAPTER = "django_hotels.location_adapter.LocationAdapter"


class LocationAdapter:
    """
    Reads the fields django_hotels' own code needs off a Location
    instance.

    The default implementation assumes django_hotels' own Location
    model's shape (name, slug, lat, lng). An installer that swaps
    DJANGO_HOTELS_LOCATION_MODEL to a differently-shaped model must also
    set DJANGO_HOTELS_LOCATION_ADAPTER to a subclass overriding whichever
    of these a plain attribute read on their own model can't satisfy.
    """

    def get_name(self, location):
        return location.name

    def get_slug(self, location):
        return location.slug

    def get_lat(self, location):
        return location.lat

    def get_lng(self, location):
        return location.lng


def get_location_adapter():
    """Returns an instance of the configured LocationAdapter (the default
    one unless DJANGO_HOTELS_LOCATION_ADAPTER overrides it)."""
    path = getattr(settings, "DJANGO_HOTELS_LOCATION_ADAPTER", DEFAULT_LOCATION_ADAPTER)
    adapter_class = import_string(path)
    return adapter_class()
