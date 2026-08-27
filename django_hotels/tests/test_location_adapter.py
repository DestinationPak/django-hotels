"""
P9.3 regression coverage: Location's swappable-model wiring, the
LocationAdapter contract, and the Hotel.city -> Hotel.location backfill
migration's matching logic.
"""

import importlib
import uuid

from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TestCase, TransactionTestCase, override_settings

from django_hotels.location_adapter import LocationAdapter, get_location_adapter
from django_hotels.models import Location, get_location_model
from django_hotels.tests.factories import HotelOwnerFactory, LocationFactory, UserFactory

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


class BackfillHotelLocationsTestCase(TransactionTestCase):
    """
    Exercises the 0003 data migration's RunPython function against a
    historical Hotel model, not the live one.

    pytest.ini's own `settings.test` runs migration-free (SQLite,
    `--no-migrations`), but docker-compose.yml sets
    DJANGO_SETTINGS_MODULE=settings.common for the `web` service, and
    pytest-django honors that environment variable over the ini value
    - so this suite actually runs against MySQL, still under
    `--no-migrations`. Getting a faithful pre-0004 Hotel shape means
    replaying the real migration graph up to 0003 with
    MigrationExecutor/ProjectState (overriding MIGRATION_MODULES back
    to its default, since --no-migrations otherwise hides every app's
    migration files from the loader), then adding a `city` column to
    the live `django_hotels_hotel` table with that historical field
    definition. This is a TransactionTestCase, not a TestCase: MySQL
    can't roll back DDL inside a transaction, and TestCase wraps every
    test in one, so schema_editor.add_field() there raises
    TransactionManagementError. TransactionTestCase runs outside a
    wrapping transaction and truncates tables between tests instead,
    so the column survives across this class's tests and tearDownClass
    drops it explicitly, since nothing will roll it back on its own.
    Owner and created_by rows are created through the live factories,
    since those models are unchanged between 0003 and today and share
    the same tables as their historical counterparts; Hotel rows
    themselves are created through HistoricalHotel directly (not
    HotelFactory), since `city` is NOT NULL with no default and the
    live model's INSERT has no idea the column exists.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        with override_settings(MIGRATION_MODULES={}):
            executor = MigrationExecutor(connection)
            state = executor.loader.project_state(
                ("django_hotels", "0003_backfill_hotel_locations")
            )
        cls.HistoricalHotel = state.apps.get_model("django_hotels", "Hotel")
        cls.HistoricalLocation = state.apps.get_model("django_hotels", "Location")
        cls.historical_apps = state.apps
        cls.city_field = cls.HistoricalHotel._meta.get_field("city")

        with connection.schema_editor() as editor:
            editor.add_field(cls.HistoricalHotel, cls.city_field)

    @classmethod
    def tearDownClass(cls):
        with connection.schema_editor() as editor:
            editor.remove_field(cls.HistoricalHotel, cls.city_field)
        super().tearDownClass()

    def make_hotel(self, city, location=None):
        owner = HotelOwnerFactory()
        user = UserFactory()
        return self.HistoricalHotel.objects.create(
            name="Test Hotel",
            slug=uuid.uuid4().hex,
            owner_id=owner.pk,
            created_by_id=user.pk,
            location_id=location.pk if location else None,
            city=city,
        )

    def run_backfill(self):
        backfill_module.backfill_hotel_locations(self.historical_apps, None)

    def test_clean_match_reuses_existing_location_case_insensitively(self):
        existing = LocationFactory(name="Lahore")
        hotel = self.make_hotel(city="  LAHORE  ")

        self.run_backfill()

        hotel.refresh_from_db()
        self.assertEqual(hotel.location_id, existing.pk)

    def test_clean_match_creates_a_new_location_when_none_exists(self):
        hotel = self.make_hotel(city="Skardu")

        self.run_backfill()

        hotel.refresh_from_db()
        self.assertIsNotNone(hotel.location)
        self.assertEqual(hotel.location.name, "Skardu")

    def test_two_hotels_with_the_same_city_share_one_location(self):
        first = self.make_hotel(city="Hunza")
        second = self.make_hotel(city="Hunza")

        self.run_backfill()

        location_ids = set(
            self.HistoricalHotel.objects.filter(
                pk__in=[first.pk, second.pk]
            ).values_list("location_id", flat=True)
        )
        self.assertEqual(len(location_ids), 1)
        self.assertNotIn(None, location_ids)

    def test_blank_city_is_left_unmatched_not_dropped(self):
        hotel = self.make_hotel(city="   ")

        self.run_backfill()

        hotel.refresh_from_db()
        self.assertIsNone(hotel.location)
        self.assertEqual(hotel.city, "   ")

    def test_already_backfilled_hotel_is_left_untouched(self):
        LocationFactory(name="Karachi")
        other_location = LocationFactory(name="Islamabad")
        hotel = self.make_hotel(city="Karachi", location=other_location)

        self.run_backfill()

        hotel.refresh_from_db()
        self.assertEqual(hotel.location_id, other_location.pk)
