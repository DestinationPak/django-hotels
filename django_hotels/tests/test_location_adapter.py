"""
P9.3 regression coverage: Location's swappable-model wiring, the
LocationAdapter contract, and the Hotel.city -> Hotel.location backfill
migration's matching logic.
"""

import importlib

from django.apps import apps as live_apps
from django.test import TestCase, override_settings

from django_hotels.location_adapter import LocationAdapter, get_location_adapter
from django_hotels.models import Hotel, Location, get_location_model
from django_hotels.tests.factories import HotelFactory, LocationFactory

backfill_module = importlib.import_module(
    "django_hotels.migrations.0003_backfill_hotel_locations"
)


class StubLocationAdapter(LocationAdapter):
    """Importable-by-dotted-path stand-in for testing the
    DJANGO_HOTELS_LOCATION_ADAPTER override - import_string() can't
    resolve a class defined inside a test method's local scope."""


class LocationSwappableTestCase(TestCase):
    def test_location_meta_swappable_setting_name(self):
        self.assertEqual(Location._meta.swappable, "DJANGO_HOTELS_LOCATION_MODEL")

    def test_unswapped_by_default(self):
        self.assertIsNone(Location._meta.swapped)

    def test_get_location_model_returns_location_by_default(self):
        self.assertIs(get_location_model(), Location)


class LocationAdapterTestCase(TestCase):
    def setUp(self):
        self.location = LocationFactory(name="Hunza", lat="36.3167", lng="74.65")
        self.adapter = LocationAdapter()

    def test_get_name(self):
        self.assertEqual(self.adapter.get_name(self.location), "Hunza")

    def test_get_slug(self):
        self.assertEqual(self.adapter.get_slug(self.location), self.location.slug)

    def test_get_lat_and_lng(self):
        self.assertEqual(self.adapter.get_lat(self.location), "36.3167")
        self.assertEqual(self.adapter.get_lng(self.location), "74.65")


class GetLocationAdapterTestCase(TestCase):
    def test_defaults_to_location_adapter(self):
        adapter = get_location_adapter()
        self.assertIsInstance(adapter, LocationAdapter)

    def test_honors_django_hotels_location_adapter_override(self):
        with override_settings(
            DJANGO_HOTELS_LOCATION_ADAPTER=(
                "django_hotels.tests.test_location_adapter.StubLocationAdapter"
            )
        ):
            adapter = get_location_adapter()

        self.assertIsInstance(adapter, StubLocationAdapter)


class BackfillHotelLocationsTestCase(TestCase):
    """
    Exercises the 0003 data migration's RunPython function directly
    against the live app registry - pytest's --no-migrations setup
    means the "historical" apps.get_model(...) resolves to exactly the
    same Hotel/Location classes as normal test code would use.
    """

    def test_clean_match_reuses_existing_location_case_insensitively(self):
        existing = LocationFactory(name="Lahore")
        hotel = HotelFactory(city="  LAHORE  ")

        backfill_module.backfill_hotel_locations(live_apps, None)

        hotel.refresh_from_db()
        self.assertEqual(hotel.location_id, existing.pk)

    def test_clean_match_creates_a_new_location_when_none_exists(self):
        hotel = HotelFactory(city="Skardu")

        backfill_module.backfill_hotel_locations(live_apps, None)

        hotel.refresh_from_db()
        self.assertIsNotNone(hotel.location)
        self.assertEqual(hotel.location.name, "Skardu")

    def test_two_hotels_with_the_same_city_share_one_location(self):
        HotelFactory(city="Hunza")
        HotelFactory(city="Hunza")

        backfill_module.backfill_hotel_locations(live_apps, None)

        location_ids = set(
            Hotel.objects.filter(city="Hunza").values_list("location_id", flat=True)
        )
        self.assertEqual(len(location_ids), 1)
        self.assertNotIn(None, location_ids)

    def test_blank_city_is_left_unmatched_not_dropped(self):
        hotel = HotelFactory(city="   ")

        backfill_module.backfill_hotel_locations(live_apps, None)

        hotel.refresh_from_db()
        self.assertIsNone(hotel.location)
        self.assertEqual(hotel.city, "   ")

    def test_already_backfilled_hotel_is_left_untouched(self):
        location = LocationFactory(name="Karachi")
        other_location = LocationFactory(name="Islamabad")
        hotel = HotelFactory(city="Karachi", location=other_location)

        backfill_module.backfill_hotel_locations(live_apps, None)

        hotel.refresh_from_db()
        self.assertEqual(hotel.location_id, other_location.pk)
        self.assertNotEqual(hotel.location_id, location.pk)
