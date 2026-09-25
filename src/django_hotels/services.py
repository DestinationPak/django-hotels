"""Business rules for hotel bookings, independent of any API layer."""

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import F

from django_hotels.choices import HotelBookingStatus
from django_hotels.models import HotelAvailability, HotelBooking

NOT_OPEN = "This date is not open for booking."
SOLD_OUT = "No rooms left on this date."
ALREADY_CANCELLED = "Booking is already cancelled."
CANNOT_BE_CANCELLED = "Booking cannot be cancelled."


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
    Book one room for `guests` on one dated room availability.

    Prices the booking at the availability's effective price per guest and
    takes one room off `rooms_available`. Raises a ValidationError keyed by
    `availability` when the date is past or its hotel isn't open for
    booking, or when no rooms are left. The check and the update happen
    under a row lock, so two bookings can't both take the last room.
    """
    with transaction.atomic():
        availability = (
            HotelAvailability.objects.open()
            .select_for_update()
            .select_related("room_type")
            .filter(pk=availability.pk)
            .first()
        )
        if availability is None:
            raise ValidationError({"availability": NOT_OPEN})
        if availability.rooms_available < 1:
            raise ValidationError({"availability": SOLD_OUT})

        booking = HotelBooking.objects.create(
            availability=availability,
            full_name=full_name,
            email=email,
            phone_number=phone_number,
            guests=guests,
            message=message,
            created_by=created_by,
            total_price=availability.effective_price * guests,
        )
        availability.rooms_available -= 1
        availability.save(update_fields=["rooms_available"])

    return booking


def _give_room_back(booking):
    HotelAvailability.objects.filter(pk=booking.availability_id).update(
        rooms_available=F("rooms_available") + 1
    )


def cancel_hotel_booking(booking, *, check_cancellable=True):
    """
    Cancel `booking` and give its room back to the availability.

    Raises a ValidationError when the booking is already cancelled, or when
    `check_cancellable` is set and its status no longer allows a guest or
    owner to cancel. Staff tools pass `check_cancellable=False` to cancel a
    confirmed booking too.
    """
    if HotelBookingStatus.is_cancelled(booking.status):
        raise ValidationError(ALREADY_CANCELLED)
    if check_cancellable and not HotelBookingStatus.can_be_cancelled(booking.status):
        raise ValidationError(CANNOT_BE_CANCELLED)

    with transaction.atomic():
        booking.status = HotelBookingStatus.CANCELLED
        booking.save(update_fields=["status", "updated_at"])
        _give_room_back(booking)

    return booking


def delete_hotel_booking(booking):
    """Delete `booking`, first giving its room back unless it was cancelled."""
    with transaction.atomic():
        if not HotelBookingStatus.is_cancelled(booking.status):
            _give_room_back(booking)
        booking.delete()
