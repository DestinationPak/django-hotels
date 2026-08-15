# Django Hotels API

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

## Local development

All commands assume Docker (`make dev.up`, `make update_db`, `make test`) — see the Makefile
for the full command list (`make help`).

## Generate demo data

```
./manage.py generate_hotels --batch_size=10
```
