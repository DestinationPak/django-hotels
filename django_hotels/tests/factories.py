"""
Test fixtures for django_hotels' models - mirrors
django_trips/tests/factories.py one vertical over, so consuming
projects (and this package's own tests) build fixtures the same way
regardless of which vertical they're testing.
"""

from datetime import timedelta

import factory
from django.contrib.auth import get_user_model
from django.utils import timezone
from factory.django import DjangoModelFactory

from django_hotels.models import (
    Hotel,
    HotelAvailability,
    HotelBooking,
    HotelOwner,
    HotelRoomType,
    Location,
)

User = get_user_model()

USER_PASSWORD = "pswd"


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User
        django_get_or_create = ("username",)

    username = factory.Sequence(lambda n: f"user-{n}")
    email = factory.Faker("email")
    password = factory.PostGenerationMethodCall("set_password", USER_PASSWORD)


class HotelOwnerFactory(DjangoModelFactory):
    class Meta:
        model = HotelOwner

    name = factory.Faker("company")
    description = factory.Faker("text")
    email = factory.Faker("email")
    mobile = factory.Faker("numerify", text="+92##########")
    cancellation_policy = factory.LazyFunction(
        lambda: [{"policy": "Non-refundable", "days": 0}]
    )
    refund_policy = factory.LazyFunction(
        lambda: [{"policy": "Full refund", "days": 7}]
    )
    verified = True


class LocationFactory(DjangoModelFactory):
    class Meta:
        model = Location
        django_get_or_create = ("name",)

    name = factory.Faker("city")
    lat = factory.Faker("latitude")
    lng = factory.Faker("longitude")


class HotelFactory(DjangoModelFactory):
    class Meta:
        model = Hotel

    name = factory.Faker("company")
    owner = factory.SubFactory(HotelOwnerFactory)
    location = factory.SubFactory(LocationFactory)
    description = factory.Faker("text")
    created_by = factory.SubFactory(UserFactory)


class HotelRoomTypeFactory(DjangoModelFactory):
    class Meta:
        model = HotelRoomType

    hotel = factory.SubFactory(HotelFactory)
    name = factory.Faker(
        "random_element", elements=["Standard", "Deluxe", "Suite"]
    )
    base_price = factory.Faker("random_int", min=2000, max=20000)
    max_occupancy = factory.Faker("random_int", min=1, max=6)


class HotelAvailabilityFactory(DjangoModelFactory):
    class Meta:
        model = HotelAvailability

    room_type = factory.SubFactory(HotelRoomTypeFactory)
    date = factory.Sequence(
        lambda n: (timezone.now() + timedelta(days=7 + n)).date()
    )
    rooms_available = factory.Faker("random_int", min=1, max=10)


class HotelBookingFactory(DjangoModelFactory):
    """
    Leaves `number`/`otp` unset - `HotelBooking.save()` auto-generates
    both, same as `TripBookingFactory` does for `TripBooking`. Pass
    `number=` explicitly when a test needs a stable, predictable
    reference to assert against.
    """

    class Meta:
        model = HotelBooking

    availability = factory.SubFactory(HotelAvailabilityFactory)
    full_name = factory.Faker("name")
    email = factory.Faker("email")
    phone_number = factory.Faker("phone_number")
    guests = factory.Faker("random_int", min=1, max=4)
    created_by = factory.SubFactory(UserFactory)
