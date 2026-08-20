from rest_framework import generics
from rest_framework.exceptions import NotFound
from rest_framework.permissions import AllowAny

from django_hotels.api.serializers import HotelBookingCreateSerializer, HotelBookingLookupSerializer
from django_hotels.models import HotelBooking


class HotelBookingCreateView(generics.CreateAPIView):
    """Guest booking - no auth required, mirrors django-trips' TripBookingCreateView."""

    permission_classes = [AllowAny]
    serializer_class = HotelBookingCreateSerializer


class HotelBookingLookupView(generics.RetrieveAPIView):
    """Anonymous booking lookup by `number` + `email` - never by number alone."""

    permission_classes = [AllowAny]
    serializer_class = HotelBookingLookupSerializer

    def get_object(self):
        number = self.request.query_params.get("number")
        email = self.request.query_params.get("email")
        booking = HotelBooking.objects.filter(number=number, email=email).first()
        if not booking:
            raise NotFound("No booking found for that reference number and email.")
        return booking
