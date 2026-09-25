# Architecture

django-hotels ships models, querysets, business rules (`services.py`) and admin for hotels, room types, availability and bookings. It has no API, views or URLs (the DRF API was removed in 1.0.0): each project builds its own endpoints on the services and querysets. It is the Hotels sibling of [django-trips](https://github.com/DestinationPak/django-trips) and follows the same structure.

Not built yet: reviews.

## Domain model

```
HotelOwner (the business or brand, like django_trips.Host)
  └── Hotel (one bookable property, like Trip)
        ├── HotelImage
        └── HotelRoomType (a room category, like TripPackage)
              └── HotelAvailability (one dated, priced date with rooms_available, like TripSchedule)
                    └── HotelBooking (like TripBooking: a DPH######NN reference,
                        guest or signed-in, created_by nullable)
```

## No ownership or permissions here

The package has no idea which user may manage a `HotelOwner`: no membership model, no scoped querysets, no permission classes. That layer belongs to the project that installs the app. Don't add auth, permission or membership code here.

## Location is swappable

`Location` has plain `name`/`slug`/`lat`/`lng` and no hierarchy (unlike django-trips' `type`/`parent`). It is swappable via `swapper` (see the README's "Custom Location model"), like django-trips.

- `Hotel.location` (nullable FK) is the only location field. The old free-text `Hotel.city` was backfilled into it (`0003_backfill_hotel_locations.py`) and dropped (`0004_remove_hotel_city.py`).
- Consumers read location fields through `django_hotels/location_adapter.py` (`get_location_adapter()`, `DJANGO_HOTELS_LOCATION_ADAPTER`).
- `AbstractLocation` (`models.py`) is a plain abstract model (like `AbstractUser`) that an installer can inherit instead of writing a `LocationAdapter` subclass.

## Business rules

Writes live in `services.py` and reads in the querysets in `managers.py`, so every consumer's API, command or admin action behaves the same.

- `create_hotel_booking()` books one room on one `HotelAvailability`: under a row lock on an `open()` availability, it refuses a past or closed date (`NOT_OPEN`) or one with no rooms left (`SOLD_OUT`), prices the booking at `effective_price` times guests, and takes one room off `rooms_available`.
- `cancel_hotel_booking()` refuses an already cancelled booking and, unless `check_cancellable=False` (staff tools), one whose status no longer allows cancelling. It gives the room back.
- `delete_hotel_booking()` gives the room back unless the booking was already cancelled, then deletes it.
- A rule failure raises Django's `ValidationError`, keyed by field where there is one, for the consumer's API to turn into its own error response.

Read side:

- `Hotel.objects.active()`: active hotels with a verified owner.
- `HotelAvailability.objects.open()`: dates a guest may book whether or not rooms are left (today onwards, active room type and hotel, verified owner). `bookable()` is `open()` with a room left, earliest first.
- `HotelBooking.objects.matching_guest(number, otp=..., email=...)`: the guest lookup, never on `number` alone.

## Admin

The admin goes through the same services: setting a booking to cancelled calls `cancel_hotel_booking()`, deleting one (singly or in bulk) calls `delete_hotel_booking()`, a cancelled booking can't be reopened (`REOPEN_NOT_ALLOWED`), and a booking's `availability` is read-only once it exists, since changing it would leave room counts wrong.
