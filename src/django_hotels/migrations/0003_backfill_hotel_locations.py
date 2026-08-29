import re

import swapper
from django.db import migrations
from django.utils.text import slugify


def normalize_city_name(raw):
    """Collapse whitespace and strip - a raw Hotel.city string ready to
    match/create a Location by name."""
    return re.sub(r"\s+", " ", raw or "").strip()


def backfill_hotel_locations(apps, schema_editor):
    if swapper.is_swapped("django_hotels", "Location"):
        # A consuming project already points DJANGO_HOTELS_LOCATION_MODEL
        # at its own model - this backfill only knows how to populate the
        # package's own default Location table.
        return

    Hotel = apps.get_model("django_hotels", "Hotel")
    Location = apps.get_model("django_hotels", "Location")

    unmatched = []
    for hotel in Hotel.objects.filter(location__isnull=True):
        name = normalize_city_name(hotel.city)
        if not name:
            unmatched.append(hotel.pk)
            continue

        location = Location.objects.filter(name__iexact=name).first()
        if location is None:
            location = Location.objects.create(name=name, slug=slugify(name))

        hotel.location = location
        hotel.save(update_fields=["location"])

    if unmatched:
        print(
            f"backfill_hotel_locations: {len(unmatched)} Hotel row(s) left "
            f"unmatched (blank/whitespace-only city) - pks: {unmatched}"
        )


def noop_reverse(apps, schema_editor):
    """Leaving Hotel.location set on reverse isn't harmful - the field
    stays nullable and city is untouched - so there's nothing to undo."""


class Migration(migrations.Migration):

    dependencies = [
        ("django_hotels", "0002_location_alter_hotel_city_hotel_location"),
    ]

    operations = [
        migrations.RunPython(backfill_hotel_locations, noop_reverse),
    ]
