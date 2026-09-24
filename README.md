# Django Hotels

[![PyPI version](https://img.shields.io/pypi/v/django-hotels.svg)](https://pypi.org/project/django-hotels/)
[![Python versions](https://img.shields.io/pypi/pyversions/django-hotels.svg)](https://pypi.org/project/django-hotels/)
[![License](https://img.shields.io/pypi/l/django-hotels.svg)](https://github.com/DestinationPak/django-hotels/blob/main/LICENSE)
[![Unit Tests](https://github.com/DestinationPak/django-hotels/actions/workflows/unit-tests.yml/badge.svg)](https://github.com/DestinationPak/django-hotels/actions/workflows/unit-tests.yml)

A Django app for hotels, room types, availability, and bookings: models, querysets, business
rules and admin. It ships no API or URLs: build your own endpoints on the services and querysets
described under "Business rules" below. (The DRF API it shipped in 0.x was removed in 1.0.0;
see the changelog.)

This service is a sibling of [django-trips](https://github.com/awaisdar001/django-trips), and
is a core component of the [DestinationPak](https://destinationpak.com) project — a platform
designed to make exploring and booking adventures across Pakistan easier and more accessible.

## Installation
Simply do:
```bash
pip install django-hotels
```

## Usage
Add the app into your installed apps in your project's settings file.
```
INSTALLED_APPS = [
    ...
    'django_hotels',
]
```
## Migrate
```
python manage.py migrate
```

## Domain model

```
HotelOwner (the business/brand)
  └── Hotel (one bookable property)
        ├── HotelImage
        └── HotelRoomType (a room category/tier)
              └── HotelAvailability (a dated, priced, bookable instance)
                    └── HotelBooking (a guest or logged-in traveller's booking)
```

`HotelOwner`/`Hotel` deliberately carry no login/auth/permission fields — this package is
tenancy-oblivious, the same way `django-trips` is. A consuming project owns the membership
layer (who may manage which `HotelOwner`), not this library.

## Business rules

The booking and availability rules live in `django_hotels.services` and the model querysets, so
any caller (your own API, a management command, the admin) gets the same behaviour:

```python
from django_hotels.models import HotelAvailability, HotelBooking
from django_hotels.services import create_hotel_booking

open_dates = HotelAvailability.objects.bookable()          # in stock, active, verified owner
booking = create_hotel_booking(
    availability, full_name="Ayesha Khan", email="ayesha@example.com",
    phone_number="+923001234567", guests=2,
)                                                            # priced per guest
found = HotelBooking.objects.matching_guest(number, email="ayesha@example.com")
```

`matching_guest` never matches on the booking number alone: it needs the `otp` or the `email`
as well, so a guessed number can't reveal someone else's booking. `create_hotel_booking` doesn't
check or reduce `rooms_available` yet.

## Custom Location model

`django_hotels.Location` (a plain `name`/`slug`/`lat`/`lng` model, no region/parent hierarchy)
is swappable, the same way Django's own `AUTH_USER_MODEL` is - if your project already has its
own location/city model, you don't have to duplicate location data into a second table just to
install this app.

Two settings, both optional and both defaulting to this package's own bundled model:

- **`DJANGO_HOTELS_LOCATION_MODEL`** - an `"app_label.ModelName"` string naming which model
  actually satisfies `Hotel.location`, e.g. `DJANGO_HOTELS_LOCATION_MODEL = "myapp.City"`. Your
  model doesn't need to share `Location`'s field names.
- **`DJANGO_HOTELS_LOCATION_ADAPTER`** - a dotted path to a `django_hotels.location_adapter
  .LocationAdapter` subclass telling this app how to read your model's fields as if they were
  `Location`'s (`get_name`, `get_slug`, `get_lat`, `get_lng`). Every place this app reads a
  location goes through `django_hotels.location_adapter.get_location_adapter()`, never by field
  name directly, so your adapter is the only place that needs to know your model's real shape.

Building a brand-new Location model rather than reusing one you already have? Inherit
`django_hotels.models.AbstractLocation` instead of writing an adapter - it's a plain abstract
Django model (the same shape `AbstractUser` is - real fields and concrete methods, not an
interface class) already carrying `name`/`slug`/`lat`/`lng` and their read methods, so you get
a working swap with no `DJANGO_HOTELS_LOCATION_ADAPTER` at all:

```python
# myapp/models.py
from django_hotels.models import AbstractLocation

class MyLocation(AbstractLocation):
    city_code = models.CharField(max_length=10)
```

```python
# settings.py
DJANGO_HOTELS_LOCATION_MODEL = "myapp.MyLocation"
```

Reusing an existing model instead - one you can't restructure, or one shared with other
libraries - stick with the adapter approach above; that's what it's for.

**Set both before your project's first `migrate`.** Like `AUTH_USER_MODEL`, this is a
swappable-model setting - Django resolves it once when the app loads, and a swap made after
`Location`'s own table has already been created doesn't retroactively move existing data.

`Hotel.location` is the only location field on `Hotel` now - the original free-text `Hotel.city`
field has been dropped. If you're upgrading from a version that still had it, a prior migration
best-effort backfilled `location` from each existing `city` string (matching or creating a
`Location` by name) before `city` itself was removed.

For a worked example of a real swap: the DestinationPakistan platform (this package's own
primary consumer, a private project) points this setting directly at its own `public.Location`
model, with no adapter override at all - `public.Location` already has `name`/`slug`/`lat`, plus
an `lng` property alias (its own field is `lon`, matching django-trips' naming), so the default
`LocationAdapter` reads it correctly with no subclass. See `docs/location-model-swap-design.md`
in that project for the full writeup.

## Local development

All commands assume Docker (`make dev.up`, `make update_db`, `make test`) — see the Makefile
for the full command list (`make help`).

## Generate demo data

```
./manage.py generate_hotels --batch_size=10
```

## Documentation

This README is also published as browsable docs (`docs/`, built with Sphinx). Build it
locally with:
```bash
pip install -e ".[docs]"
sphinx-build -b html docs docs/_build
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for the development/release workflow, and the
[Code of Conduct](CODE_OF_CONDUCT.md). Found a security issue? See
[SECURITY.md](SECURITY.md) rather than opening a public issue.
