from datetime import timedelta

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils.timezone import localdate

from django_hotels.choices import HotelBookingStatus
from django_hotels.models import HotelAvailability, HotelBooking
from django_hotels.services import (
    ALREADY_CANCELLED,
    CANNOT_BE_CANCELLED,
    NOT_OPEN,
    SOLD_OUT,
    cancel_hotel_booking,
    create_hotel_booking,
)
from django_hotels.tests.factories import HotelAvailabilityFactory, HotelBookingFactory, UserFactory


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

    def test_takes_one_room_off_the_availability(self):
        availability = HotelAvailabilityFactory(rooms_available=2)

        create_hotel_booking(availability, guests=3, **self.guest)

        availability.refresh_from_db()
        self.assertEqual(availability.rooms_available, 1)

    def test_rejects_a_sold_out_date(self):
        availability = HotelAvailabilityFactory(rooms_available=1)
        create_hotel_booking(availability, **self.guest)

        with self.assertRaises(ValidationError) as ctx:
            create_hotel_booking(availability, **self.guest)

        self.assertEqual(ctx.exception.message_dict, {"availability": [SOLD_OUT]})
        self.assertEqual(HotelBooking.objects.count(), 1)

    def test_checks_the_stored_count_not_the_passed_instance(self):
        availability = HotelAvailabilityFactory(rooms_available=1)
        stale = HotelAvailability.objects.get(pk=availability.pk)
        create_hotel_booking(availability, **self.guest)

        with self.assertRaises(ValidationError):
            create_hotel_booking(stale, **self.guest)


    def test_rejects_a_past_date(self):
        availability = HotelAvailabilityFactory(date=localdate() - timedelta(days=1), rooms_available=3)

        with self.assertRaises(ValidationError) as ctx:
            create_hotel_booking(availability, **self.guest)

        self.assertEqual(ctx.exception.message_dict, {"availability": [NOT_OPEN]})

    def test_rejects_a_date_at_an_inactive_hotel(self):
        availability = HotelAvailabilityFactory(room_type__hotel__is_active=False, rooms_available=3)

        with self.assertRaises(ValidationError) as ctx:
            create_hotel_booking(availability, **self.guest)

        self.assertEqual(ctx.exception.message_dict, {"availability": [NOT_OPEN]})
        availability.refresh_from_db()
        self.assertEqual(availability.rooms_available, 3)


class CancelHotelBookingTestCase(TestCase):
    def test_cancels_and_gives_the_room_back(self):
        booking = HotelBookingFactory(availability__rooms_available=0)

        cancel_hotel_booking(booking)

        booking.refresh_from_db()
        booking.availability.refresh_from_db()
        self.assertEqual(booking.status, HotelBookingStatus.CANCELLED)
        self.assertEqual(booking.availability.rooms_available, 1)

    def test_rejects_an_already_cancelled_booking(self):
        booking = HotelBookingFactory(
            status=HotelBookingStatus.CANCELLED, availability__rooms_available=0
        )

        with self.assertRaisesMessage(ValidationError, ALREADY_CANCELLED):
            cancel_hotel_booking(booking)

        booking.availability.refresh_from_db()
        self.assertEqual(booking.availability.rooms_available, 0)

    def test_rejects_a_confirmed_booking(self):
        booking = HotelBookingFactory(status=HotelBookingStatus.CONFIRMED)

        with self.assertRaisesMessage(ValidationError, CANNOT_BE_CANCELLED):
            cancel_hotel_booking(booking)
