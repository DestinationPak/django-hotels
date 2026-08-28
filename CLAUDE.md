# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this
repository.

## What this is

`django-hotels` is a reusable Django app (published as a pip package, see `setup.cfg`)
providing a REST API for managing hotels, room types, availability, and bookings. It's the
Hotels-vertical sibling of [django-trips](https://github.com/awaisdar001/django-trips), and is
part of the [DestinationPak](https://destinationpak.com) platform.

Note the two similarly-named top-level packages: `django-hotels/` (hyphen) is the throwaway
Django *project* shell used only for local dev (`urls.py`/`wsgi.py`/`asgi.py`); `django_hotels/`
(underscore) is the actual app that gets published and contains all real logic.

This is a basic initial scaffold — models, a read-only public catalog API, and a guest booking
flow exist; nothing beyond that has been built yet (no schema/swagger docs, no reviews, no
staff-facing management endpoints).

## Common commands

All development happens inside Docker; there is no supported bare-metal workflow (mirrors
django-trips).

```bash
make build          # docker compose build (destroys existing containers first)
make dev.up         # start web + mysql containers
make shell          # attach a shell inside the web container
make update_db      # run migrations
make random_hotels  # seed random hotels (generate_hotels --batch_size=10)
make test           # docker compose run --rm web pytest
make stop / make destroy
```

## Architecture

### Domain model shape

```
HotelOwner (the business/brand, mirrors django_trips.Host)
  └── Hotel (one bookable property, mirrors Trip)
        ├── HotelImage
        └── HotelRoomType (a room category/tier, mirrors TripPackage)
              └── HotelAvailability (dated/priced/bookable, mirrors TripSchedule)
                    └── HotelBooking (mirrors TripBooking - auto-generated DPH######NN
                        reference number, guest or logged-in, `created_by` nullable)
```

**This package is deliberately tenancy-oblivious**, the same way `django_trips` is — it has no
concept of which user may manage a `HotelOwner`, no scoped querysets, no permission classes
tied to ownership. That membership/authorization layer belongs to whatever project installs
this app (e.g. destipak's `djangoapps/hotel_owners/`, mirroring its existing
`djangoapps/trip_hosts/` for Trips), never to this library itself.

`Location` (plain `name`/`slug`/`lat`/`lng`, no hierarchy - unlike `django_trips.Location`'s
`type`/`parent`) is swappable via `swapper` (see README's "Custom Location model"), the same
mechanism `django_trips.Location` uses. `Hotel.location` is a new, nullable FK added alongside
the pre-existing `Hotel.city` `CharField` — `city` is **not yet removed**; a data migration
(`migrations/0003_backfill_hotel_locations.py`) best-effort backfills `location` from `city` by
name, and `city` only gets dropped once every consumer (destipak included) has finished
backfilling against its own chosen Location model. `django_hotels/location_adapter.py`
(`LocationAdapter`/`get_location_adapter()`, `DJANGO_HOTELS_LOCATION_ADAPTER`) is the read path
for location fields, mirroring `django_trips/location_adapter.py` one vertical over - nothing
in this package's own serializers reads `location`'s fields yet (`city` is still what's
exposed), so the adapter exists as the swap-point infrastructure, ready for whichever consumer
project (or a later ticket here) actually surfaces `location` in output. `AbstractLocation`
(`models.py`) is a plain abstract Django model - the same shape `AbstractUser` is, real fields
and concrete methods, not an interface class - an installer building a brand-new custom
Location model can inherit directly instead of writing a `LocationAdapter` subclass; see
README's "Custom Location model" for when to reach for which.

### API layer

`django_hotels/api/urls.py` wires a DRF `DefaultRouter` for `HotelViewSet` (read-only, public,
`ReadOnlyModelViewSet` — no create/update/destroy in this package, matching django-trips'
post-hardening `TripViewSet`) plus explicit booking create/lookup endpoints
(`HotelBookingCreateView` is `AllowAny` — guest booking is a product requirement;
`HotelBookingLookupView` requires both `number` and `email`, never `number` alone).

### Settings

`settings/common.py` is the real settings module (Docker sets
`DJANGO_SETTINGS_MODULE=settings.common`); `settings/test.py` just re-exports it for pytest.
`django-hotels/wsgi.py`/`asgi.py`/`urls.py` are the minimal dev-only project shell and aren't
part of the published package.

## Testing conventions

New tests are written as `django.test.TestCase` subclasses, not bare
`@pytest.mark.django_db`-decorated functions - matches `djangoapps/hotel_owners`' convention in
destipak and `django_rentals`' one vertical over. `django_hotels/tests/test_models.py` and
`django_hotels/api/tests/*.py` predate this convention and haven't been retrofitted - don't take
their function-style shape as the pattern to follow for new tests.

Build test fixtures via `django_hotels/tests/factories.py` (`HotelOwnerFactory`,
`HotelFactory`, `HotelRoomTypeFactory`, `HotelAvailabilityFactory`, `HotelBookingFactory`,
`UserFactory`) rather than calling `Model.objects.create(...)` directly in a test - mirrors
`django_trips/tests/factories.py`'s existing convention one vertical over. Consuming projects
(destipak's `djangoapps/hotel_owners/`) should do the same when their own tests need a Hotel/
HotelOwner/HotelBooking fixture, since this module is importable wherever the package is
installed (it's shipped as part of `django_hotels`, not test-only-excluded). A raw
`.objects.create()` is still fine for a test whose whole point is model/manager mechanics.
