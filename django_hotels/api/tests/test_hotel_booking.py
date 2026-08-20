"""
Guest hotel-booking create/lookup, and authenticated retrieve/update.

Mirrors django_trips' booking IDOR fix (Section 4 of the design doc):
these regression tests are written alongside the endpoints, not after
(P0.1/P0.5's own rule), so a future refactor can't silently reopen the
same hole - a booking must never be readable/writable by anyone other
than the guest who proves ownership (lookup) or the user who created
it (retrieve/update).
"""

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient

from django_hotels.models import Hotel, HotelAvailability, HotelBooking, HotelOwner, HotelRoomType

User = get_user_model()


@pytest.fixture
def availability(db):
    owner = HotelOwner.objects.create(name="Karakoram Stays", verified=True)
    creator = User.objects.create(username="staff")
    hotel = Hotel.objects.create(name="Hunza Serena", owner=owner, city="Hunza", created_by=creator)
    room_type = HotelRoomType.objects.create(hotel=hotel, name="Standard", base_price=5000)
    return HotelAvailability.objects.create(room_type=room_type, date="2026-09-01")


@pytest.fixture
def booking(availability):
    return HotelBooking.objects.create(
        availability=availability,
        full_name="Jane Traveller",
        email="jane@example.com",
        phone_number="+923001234567",
    )


@pytest.mark.django_db
def test_create_requires_no_auth(availability):
    response = APIClient().post(
        reverse("hotels-api:bookings-create"),
        {
            "availability": availability.id,
            "full_name": "Guest Traveller",
            "email": "guest@example.com",
            "phone_number": "+923009999999",
        },
    )
    assert response.status_code == 201


@pytest.mark.django_db
def test_lookup_requires_number_and_email_or_otp(booking):
    """The core IDOR regression: a bare number must never resolve a booking."""
    response = APIClient().get(
        reverse("hotels-api:bookings-lookup"), {"number": booking.number}
    )
    assert response.status_code == 400


@pytest.mark.django_db
def test_lookup_by_number_and_correct_email_succeeds(booking):
    response = APIClient().get(
        reverse("hotels-api:bookings-lookup"),
        {"number": booking.number, "email": booking.email.upper()},
    )
    assert response.status_code == 200
    assert response.data["number"] == booking.number


@pytest.mark.django_db
def test_lookup_by_number_and_otp_succeeds(booking):
    response = APIClient().get(
        reverse("hotels-api:bookings-lookup"),
        {"number": booking.number, "otp": booking.otp},
    )
    assert response.status_code == 200


@pytest.mark.django_db
def test_lookup_by_number_and_wrong_email_fails(booking):
    response = APIClient().get(
        reverse("hotels-api:bookings-lookup"),
        {"number": booking.number, "email": "someone-else@example.com"},
    )
    assert response.status_code == 404


@pytest.mark.django_db
def test_retrieve_requires_authentication(booking):
    url = reverse("hotels-api:booking-detail", kwargs={"number": booking.number})
    response = APIClient().get(url)
    assert response.status_code in (401, 403)


@pytest.mark.django_db
def test_retrieve_scoped_to_owner(availability):
    owner_user = User.objects.create(username="owner-traveller")
    own_booking = HotelBooking.objects.create(
        availability=availability,
        full_name="Owner Traveller",
        email="owner@example.com",
        phone_number="+923001112222",
        created_by=owner_user,
    )
    client = APIClient()
    client.force_authenticate(owner_user)
    url = reverse("hotels-api:booking-detail", kwargs={"number": own_booking.number})

    response = client.get(url)

    assert response.status_code == 200
    assert response.data["number"] == own_booking.number
    assert "otp" not in response.data


@pytest.mark.django_db
def test_retrieve_other_users_booking_returns_404(availability):
    """A booking must only be readable by the user who created it (IDOR regression)."""
    owner_user = User.objects.create(username="owner-traveller-2")
    other_users_booking = HotelBooking.objects.create(
        availability=availability,
        full_name="Owner Traveller",
        email="owner2@example.com",
        phone_number="+923001112223",
        created_by=owner_user,
    )
    attacker = User.objects.create(username="attacker")
    client = APIClient()
    client.force_authenticate(attacker)
    url = reverse(
        "hotels-api:booking-detail", kwargs={"number": other_users_booking.number}
    )

    response = client.get(url)

    assert response.status_code == 404


@pytest.mark.django_db
def test_update_scoped_to_owner(availability):
    owner_user = User.objects.create(username="owner-traveller-3")
    own_booking = HotelBooking.objects.create(
        availability=availability,
        full_name="Owner Traveller",
        email="owner3@example.com",
        phone_number="+923001112224",
        created_by=owner_user,
    )
    client = APIClient()
    client.force_authenticate(owner_user)
    url = reverse("hotels-api:booking-detail", kwargs={"number": own_booking.number})

    response = client.put(
        url,
        {
            "availability": availability.id,
            "full_name": "Owner Traveller Updated",
            "email": own_booking.email,
            "phone_number": own_booking.phone_number,
        },
    )

    assert response.status_code == 200
    own_booking.refresh_from_db()
    assert own_booking.full_name == "Owner Traveller Updated"


@pytest.mark.django_db
def test_update_other_users_booking_returns_404(availability):
    """A booking must only be writable by the user who created it (IDOR regression)."""
    owner_user = User.objects.create(username="owner-traveller-4")
    other_users_booking = HotelBooking.objects.create(
        availability=availability,
        full_name="Owner Traveller",
        email="owner4@example.com",
        phone_number="+923001112225",
        created_by=owner_user,
    )
    attacker = User.objects.create(username="attacker-2")
    client = APIClient()
    client.force_authenticate(attacker)
    url = reverse(
        "hotels-api:booking-detail", kwargs={"number": other_users_booking.number}
    )

    response = client.put(
        url,
        {
            "availability": availability.id,
            "full_name": "Hijacked",
            "email": other_users_booking.email,
            "phone_number": other_users_booking.phone_number,
        },
    )

    assert response.status_code == 404
    other_users_booking.refresh_from_db()
    assert other_users_booking.full_name == "Owner Traveller"
