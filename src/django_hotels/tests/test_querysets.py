from datetime import timedelta

from django.test import TestCase
from django.utils.timezone import localdate

from django_hotels.models import HotelAvailability, HotelBooking
from django_hotels.tests.factories import HotelAvailabilityFactory, HotelBookingFactory


class BookableAvailabilityTestCase(TestCase):
    def test_includes_open_dates_on_active_verified_hotels(self):
        availability = HotelAvailabilityFactory(rooms_available=2)

        self.assertEqual(list(HotelAvailability.objects.bookable()), [availability])

    def test_leaves_out_sold_out_dates(self):
        HotelAvailabilityFactory(rooms_available=0)

        self.assertFalse(HotelAvailability.objects.bookable().exists())

    def test_leaves_out_inactive_room_types(self):
        HotelAvailabilityFactory(room_type__is_active=False)

        self.assertFalse(HotelAvailability.objects.bookable().exists())

    def test_leaves_out_inactive_hotels(self):
        HotelAvailabilityFactory(room_type__hotel__is_active=False)

        self.assertFalse(HotelAvailability.objects.bookable().exists())

    def test_leaves_out_hotels_whose_owner_is_not_verified(self):
        HotelAvailabilityFactory(room_type__hotel__owner__verified=False)

        self.assertFalse(HotelAvailability.objects.bookable().exists())


    def test_leaves_out_past_dates(self):
        HotelAvailabilityFactory(date=localdate() - timedelta(days=1), rooms_available=2)

        self.assertFalse(HotelAvailability.objects.bookable().exists())


class OpenAvailabilityTestCase(TestCase):
    def test_keeps_sold_out_dates(self):
        availability = HotelAvailabilityFactory(rooms_available=0)

        self.assertEqual(list(HotelAvailability.objects.open()), [availability])

    def test_includes_today(self):
        availability = HotelAvailabilityFactory(date=localdate())

        self.assertEqual(list(HotelAvailability.objects.open()), [availability])

    def test_leaves_out_past_dates(self):
        HotelAvailabilityFactory(date=localdate() - timedelta(days=1))

        self.assertFalse(HotelAvailability.objects.open().exists())


class MatchingGuestTestCase(TestCase):
    def setUp(self):
        super().setUp()
        self.booking = HotelBookingFactory(email="guest@example.com")

    def test_matches_number_and_otp(self):
        matches = HotelBooking.objects.matching_guest(
            self.booking.number, otp=self.booking.otp
        )

        self.assertEqual(list(matches), [self.booking])

    def test_matches_number_and_email_ignoring_case(self):
        matches = HotelBooking.objects.matching_guest(
            self.booking.number, email="GUEST@example.com"
        )

        self.assertEqual(list(matches), [self.booking])

    def test_never_matches_on_number_alone(self):
        self.assertFalse(HotelBooking.objects.matching_guest(self.booking.number).exists())

    def test_a_wrong_second_factor_matches_nothing(self):
        matches = HotelBooking.objects.matching_guest(
            self.booking.number, email="someone@else.com"
        )

        self.assertFalse(matches.exists())
