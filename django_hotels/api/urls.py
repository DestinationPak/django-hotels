from django.urls import path
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from rest_framework.routers import DefaultRouter

from django_hotels.api.views import booking, hotel

app_name = "hotels-api"

router = DefaultRouter()
router.register(r"hotels", hotel.HotelViewSet, basename="hotel")
router.register(
    r"bookings", booking.HotelBookingRetrieveUpdateViewSet, basename="booking"
)

app_urlpatterns = [
    path(
        "owners/",
        hotel.ActiveHotelOwnersListAPIView.as_view(),
        name="owners",
    ),
    path(
        "bookings/create/",
        booking.HotelBookingCreateView.as_view(),
        name="bookings-create",
    ),
    path(
        "bookings/lookup/",
        booking.HotelBookingLookupView.as_view(),
        name="bookings-lookup",
    ),
    *router.urls,
]

schema_urls = [
    # urlconf pins the generator to this module alone - unset, drf-spectacular walks
    # the *host* project's ROOT_URLCONF by default, so this would describe every DRF
    # view in whatever project installs this app, not just this lib's own endpoints.
    # Mirrors django_trips.api.urls' schema_urls.
    path(
        "schema/",
        SpectacularAPIView.as_view(
            urlconf="django_hotels.api.urls",
            custom_settings={
                "TITLE": "Django Hotels API",
                "DESCRIPTION": "Django Hotels management restful API",
                "VERSION": "1.0.0",
            },
        ),
        name="schema",
    ),
    path(
        "schema/swagger-ui/",
        SpectacularSwaggerView.as_view(url_name="hotels-api:schema"),
        name="swagger-ui",
    ),
    path(
        "schema/redoc/",
        SpectacularRedocView.as_view(url_name="hotels-api:schema"),
        name="redoc",
    ),
]

urlpatterns = [*app_urlpatterns, *schema_urls]
