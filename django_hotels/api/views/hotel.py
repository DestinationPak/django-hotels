from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics
from rest_framework.permissions import AllowAny
from rest_framework.viewsets import ReadOnlyModelViewSet

from django_hotels.api.filters import HotelAvailabilityFilter
from django_hotels.api.serializers import (
    HotelAvailabilitySerializer,
    HotelDetailSerializer,
    HotelListSerializer,
    HotelOwnerSerializer,
)
from django_hotels.models import Hotel, HotelAvailability, HotelOwner


class HotelViewSet(ReadOnlyModelViewSet):
    """Public, read-only catalog of published hotels - no create/update/destroy.

    Management (create/update/archive) is a consuming project's operator-surface
    job, the same architectural split django-trips uses for TripViewSet.
    """

    permission_classes = [AllowAny]
    lookup_field = "slug"
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["city", "status", "owner"]

    def get_queryset(self):
        return Hotel.objects.active().select_related("owner")

    def get_serializer_class(self):
        if self.action == "retrieve":
            return HotelDetailSerializer
        return HotelListSerializer


class ActiveHotelOwnersListAPIView(generics.ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = HotelOwnerSerializer

    def get_queryset(self):
        return HotelOwner.objects.active()


class HotelAvailabilityListAPIView(generics.ListAPIView):
    """
    Public availability search - which room types are bookable, and at
    what price, optionally filtered by hotel, room type, and/or a date
    range (see HotelAvailabilityFilter).
    """

    permission_classes = [AllowAny]
    serializer_class = HotelAvailabilitySerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = HotelAvailabilityFilter

    def get_queryset(self):
        return (
            HotelAvailability.objects.filter(
                rooms_available__gt=0,
                room_type__is_active=True,
                room_type__hotel__in=Hotel.objects.active(),
            )
            .select_related("room_type", "room_type__hotel")
            .order_by("date")
        )
