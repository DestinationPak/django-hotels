# Django Hotels API

[![PyPI version](https://img.shields.io/pypi/v/django-hotels.svg)](https://pypi.org/project/django-hotels/)
[![Python versions](https://img.shields.io/pypi/pyversions/django-hotels.svg)](https://pypi.org/project/django-hotels/)
[![License](https://img.shields.io/pypi/l/django-hotels.svg)](https://github.com/DestinationPak/django-hotels/blob/master/LICENSE)
[![Unit Tests](https://github.com/DestinationPak/django-hotels/actions/workflows/unit-tests.yml/badge.svg)](https://github.com/DestinationPak/django-hotels/actions/workflows/unit-tests.yml)

This is a Django REST API for managing and retrieving hotels, room types, availability, and
bookings.

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
Add the following to your root `urls.py` or to your desired file location.
```
urlpatterns = [
    ...
    path('hotels/', include('django_hotels.urls')),
]
```
This mounts the whole app under your own chosen namespace (`hotels/` above - replace with
whatever prefix you like) with the lib's own `v1/` version underneath it, e.g.
`hotels/v1/hotels/`. The app versions itself independently of your project's own API version.

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

**Set both before your project's first `migrate`.** Like `AUTH_USER_MODEL`, this is a
swappable-model setting - Django resolves it once when the app loads, and a swap made after
`Location`'s own table has already been created doesn't retroactively move existing data.

`Hotel.city` (the original free-text field) stays in place alongside the new `Hotel.location`
FK for now - a data migration best-effort backfills `location` from each existing `city` string
(matching or creating a `Location` by name), leaving it null wherever `city` is blank. `city`
itself is only dropped once every consumer has finished backfilling against its own chosen
Location model.

For a worked example of a real swap: the DestinationPakistan platform (this package's own
primary consumer, a private project) points this setting at its own `public.City` model via a
`HotelsRentalsCityLocationAdapter` in its `djangoapps/public/adapters.py` - the same shape
sketched above, just concretely filled in.

## Local development

All commands assume Docker (`make dev.up`, `make update_db`, `make test`) — see the Makefile
for the full command list (`make help`).

## Generate demo data

```
./manage.py generate_hotels --batch_size=10
```
