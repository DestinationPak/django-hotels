import pytest
from django.contrib.auth import get_user_model

from django_hotels.models import Hotel, HotelAvailability, HotelBooking, HotelOwner, HotelRoomType

User = get_user_model()


@pytest.mark.django_db
def test_hotel_owner_slug_auto_generated():
    owner = HotelOwner.objects.create(name="Karakoram Stays")
    assert owner.slug == "karakoram-stays"


@pytest.mark.django_db
def test_hotel_active_manager_requires_verified_owner():
    user = User.objects.create(username="staff")
    unverified_owner = HotelOwner.objects.create(name="New Owner", verified=False)
    verified_owner = HotelOwner.objects.create(name="Trusted Owner", verified=True)

    Hotel.objects.create(
        name="Unverified Inn", owner=unverified_owner, created_by=user
    )
    verified_hotel = Hotel.objects.create(
        name="Trusted Inn", owner=verified_owner, created_by=user
    )

    assert list(Hotel.objects.active()) == [verified_hotel]


@pytest.mark.django_db
def test_hotel_booking_generates_reference_number_and_otp():
    user = User.objects.create(username="staff2")
    owner = HotelOwner.objects.create(name="Owner", verified=True)
    hotel = Hotel.objects.create(name="Hotel", owner=owner, created_by=user)
    room_type = HotelRoomType.objects.create(hotel=hotel, name="Standard", base_price=5000)
    availability = HotelAvailability.objects.create(room_type=room_type, date="2026-09-01")

    booking = HotelBooking.objects.create(
        availability=availability,
        full_name="Jane Traveller",
        email="jane@example.com",
        phone_number="+923001234567",
    )

    assert booking.number.startswith("DPH")
    assert len(booking.otp) == 4
