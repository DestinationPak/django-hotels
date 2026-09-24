"""Business rules for hotel bookings, independent of any API layer."""

from django_hotels.models import HotelBooking


def create_hotel_booking(  # pylint:disable=too-many-arguments
    availability,
    *,
    full_name,
    email,
    phone_number,
    guests=1,
    message=None,
    created_by=None,
):
    """
    Book `guests` onto one dated room availability.

    Prices the booking at the availability's effective price per guest. It
    doesn't check or reduce `rooms_available` yet, so an availability can be
    over-booked.
    """
    return HotelBooking.objects.create(
        availability=availability,
        full_name=full_name,
        email=email,
        phone_number=phone_number,
        guests=guests,
        message=message,
        created_by=created_by,
        total_price=availability.effective_price * guests,
    )
