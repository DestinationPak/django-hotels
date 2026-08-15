from rest_framework import generics
from rest_framework.permissions import AllowAny
from rest_framework.viewsets import ReadOnlyModelViewSet

from django_hotels.api.serializers import (
    HotelDetailSerializer,
    HotelListSerializer,
    HotelOwnerSerializer,
)
from django_hotels.models import Hotel, HotelOwner


class HotelViewSet(ReadOnlyModelViewSet):
    """Public, read-only catalog of published hotels - no create/update/destroy.

    Management (create/update/archive) is a consuming project's operator-surface
    job, the same architectural split django-trips uses for TripViewSet.
    """

    permission_classes = [AllowAny]
    lookup_field = "slug"

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
