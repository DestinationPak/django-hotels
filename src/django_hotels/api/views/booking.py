from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework.authentication import SessionAuthentication
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.viewsets import GenericViewSet

from django_hotels.api.serializers import HotelBookingCreateSerializer, HotelBookingLookupSerializer
from django_hotels.models import HotelBooking


class HotelBookingCreateView(generics.CreateAPIView):
    """Guest booking - no auth required, mirrors django-trips' TripBookingCreateView."""

    permission_classes = [AllowAny]
    serializer_class = HotelBookingCreateSerializer


class HotelBookingLookupView(generics.RetrieveAPIView):
    """
    Anonymous "look up my booking" endpoint.

    Scoped to a booking `number` AND one more proof-of-ownership factor -
    either its 4-digit `otp` or its `email` - never `number` alone, so a
    guessed or leaked reference number can't be used to pull up someone
    else's booking. Mirrors django-trips' TripBookingLookupView fix
    (the booking IDOR, Section 4).
    """

    serializer_class = HotelBookingLookupSerializer
    permission_classes = [AllowAny]

    def get_object(self):
        number = self.request.query_params.get("number")
        otp = self.request.query_params.get("otp")
        email = self.request.query_params.get("email")

        if not number or not (otp or email):
            raise ValidationError(
                {
                    "detail": "`number` and one of `otp` or `email` query "
                    "parameters are required."
                }
            )

        bookings = HotelBooking.objects.filter(number=number)
        bookings = bookings.filter(otp=otp) if otp else bookings.filter(email__iexact=email)
        return get_object_or_404(bookings)


class HotelBookingRetrieveUpdateViewSet(GenericViewSet, generics.RetrieveUpdateAPIView):
    """
    Authenticated "my booking" retrieve/update.

    Mirrors django-trips' TripBookingRetrieveUpdateViewSet fix (the
    booking IDOR, Section 4): the queryset is scoped to
    created_by=request.user, never HotelBooking.objects.all(), so one
    user can't retrieve or update another user's booking by guessing
    its reference number.
    """

    permission_classes = [IsAuthenticated]
    authentication_classes = [SessionAuthentication]
    serializer_class = HotelBookingCreateSerializer
    lookup_field = "number"
    http_method_names = ["get", "put"]

    def get_queryset(self):
        return HotelBooking.objects.filter(created_by=self.request.user)
