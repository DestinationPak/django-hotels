"""
`HotelBookingCreateSerializer.create()`'s `created_by` assignment.

Regression coverage for P8.3.11: an authenticated request must have
`created_by` set so the booking later shows up under that user's "my
bookings" surface; a guest request must leave it null.
"""

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from django_hotels.models import HotelBooking
from django_hotels.tests.factories import HotelAvailabilityFactory, UserFactory


class HotelBookingCreateCreatedByTestCase(TestCase):
    def test_guest_create_leaves_created_by_null(self):
        availability = HotelAvailabilityFactory()

        response = APIClient().post(
            reverse("hotels-api:bookings-create"),
            {
                "availability": availability.id,
                "full_name": "Guest Traveller",
                "email": "guest@example.com",
                "phone_number": "+923009999999",
            },
        )

        self.assertEqual(response.status_code, 201, response.data)
        booking = HotelBooking.objects.get(number=response.data["number"])
        self.assertIsNone(booking.created_by)

    def test_authenticated_create_sets_created_by(self):
        availability = HotelAvailabilityFactory()
        user = UserFactory()
        client = APIClient()
        client.force_authenticate(user)

        response = client.post(
            reverse("hotels-api:bookings-create"),
            {
                "availability": availability.id,
                "full_name": "Logged In Traveller",
                "email": user.email,
                "phone_number": "+923009999998",
            },
        )

        self.assertEqual(response.status_code, 201, response.data)
        booking = HotelBooking.objects.get(number=response.data["number"])
        self.assertEqual(booking.created_by, user)
