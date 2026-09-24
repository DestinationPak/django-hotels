from django.test import TestCase

from django_hotels.services import create_hotel_booking
from django_hotels.tests.factories import HotelAvailabilityFactory, UserFactory


class CreateHotelBookingTestCase(TestCase):
    def setUp(self):
        super().setUp()
        self.guest = {
            "full_name": "Foo Bar",
            "email": "foo@bar.com",
            "phone_number": "+923331234567",
        }

    def test_prices_at_the_room_base_price_per_guest(self):
        availability = HotelAvailabilityFactory(room_type__base_price=8000, price=None)

        booking = create_hotel_booking(availability, guests=3, **self.guest)

        self.assertEqual(booking.total_price, 24000)

    def test_a_date_price_overrides_the_room_base_price(self):
        availability = HotelAvailabilityFactory(room_type__base_price=8000, price=9500)

        booking = create_hotel_booking(availability, guests=2, **self.guest)

        self.assertEqual(booking.total_price, 19000)

    def test_records_who_booked(self):
        user = UserFactory()

        booking = create_hotel_booking(
            HotelAvailabilityFactory(), created_by=user, **self.guest
        )

        self.assertEqual(booking.created_by, user)
