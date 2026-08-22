"""
HotelAvailabilityListAPIView - the public date-range availability search.

Covers HotelAvailabilityFilter's query params (hotel/room_type/date_from/
date_to) and the queryset's exclusion rules (sold-out dates, an inactive
room type, an unverified/inactive hotel).
"""

from datetime import date

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from django_hotels.tests.factories import (
    HotelAvailabilityFactory,
    HotelFactory,
    HotelOwnerFactory,
    HotelRoomTypeFactory,
)


class HotelAvailabilitySearchTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse("hotels-api:availabilities")

    def test_lists_availabilities_with_no_filters(self):
        HotelAvailabilityFactory(date=date(2030, 1, 10))
        HotelAvailabilityFactory(date=date(2030, 1, 11))

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)

    def test_filters_by_hotel_slug(self):
        hotel = HotelFactory()
        room_type = HotelRoomTypeFactory(hotel=hotel)
        matching = HotelAvailabilityFactory(room_type=room_type)
        HotelAvailabilityFactory()  # a different hotel entirely

        response = self.client.get(self.url, {"hotel": hotel.slug})

        self.assertEqual([row["id"] for row in response.data], [matching.id])

    def test_filters_by_room_type(self):
        room_type = HotelRoomTypeFactory()
        matching = HotelAvailabilityFactory(room_type=room_type)
        HotelAvailabilityFactory()  # a different room type

        response = self.client.get(self.url, {"room_type": room_type.id})

        self.assertEqual([row["id"] for row in response.data], [matching.id])

    def test_filters_by_date_range(self):
        too_early = HotelAvailabilityFactory(date=date(2030, 1, 1))
        in_range = HotelAvailabilityFactory(date=date(2030, 1, 15))
        too_late = HotelAvailabilityFactory(date=date(2030, 2, 1))

        response = self.client.get(
            self.url, {"date_from": "2030-01-10", "date_to": "2030-01-20"}
        )

        ids = {row["id"] for row in response.data}
        self.assertEqual(ids, {in_range.id})
        self.assertNotIn(too_early.id, ids)
        self.assertNotIn(too_late.id, ids)

    def test_excludes_sold_out_dates(self):
        HotelAvailabilityFactory(rooms_available=0)

        response = self.client.get(self.url)

        self.assertEqual(response.data, [])

    def test_excludes_inactive_room_type(self):
        room_type = HotelRoomTypeFactory(is_active=False)
        HotelAvailabilityFactory(room_type=room_type)

        response = self.client.get(self.url)

        self.assertEqual(response.data, [])

    def test_excludes_unverified_owner_hotel(self):
        owner = HotelOwnerFactory(verified=False)
        hotel = HotelFactory(owner=owner)
        room_type = HotelRoomTypeFactory(hotel=hotel)
        HotelAvailabilityFactory(room_type=room_type)

        response = self.client.get(self.url)

        self.assertEqual(response.data, [])

    def test_row_shape_nests_room_type_and_hotel_slug(self):
        hotel = HotelFactory()
        room_type = HotelRoomTypeFactory(hotel=hotel, name="Deluxe")
        HotelAvailabilityFactory(room_type=room_type)

        response = self.client.get(self.url)

        row = response.data[0]
        self.assertEqual(row["room_type"]["name"], "Deluxe")
        self.assertEqual(row["room_type"]["hotel"], hotel.slug)
