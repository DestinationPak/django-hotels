"""Urls for hotels app"""

from django.urls import include, path

urlpatterns = [
    path(
        # The lib owns its own version, independent of whatever prefix/version scheme
        # the consuming project uses for its own endpoints - see README "Usage".
        "v1/",
        include(("django_hotels.api.urls", "hotels-api"), namespace="hotels-api"),
    ),
]
