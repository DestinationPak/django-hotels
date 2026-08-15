from django.urls import path
from rest_framework.routers import DefaultRouter

from django_hotels.api.views import booking, hotel

app_name = "hotels-api"

router = DefaultRouter()
router.register(r"hotels", hotel.HotelViewSet, basename="hotel")

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

urlpatterns = app_urlpatterns
