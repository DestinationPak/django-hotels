"""Business rules for hotel bookings, independent of any API layer."""

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import F

from django_hotels.choices import HotelBookingStatus
from django_hotels.models import HotelAvailability, HotelBooking

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
    `availability` when no rooms are left. The check and the update happen
    under a row lock, so two bookings can't both take the last room.
    """
    with transaction.atomic():
        availability = (
            HotelAvailability.objects.select_for_update()
            .select_related("room_type")
            .get(pk=availability.pk)
        )
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


def cancel_hotel_booking(booking):
    """
    Cancel `booking` and give its room back to the availability.

    Raises a ValidationError when the booking is already cancelled or its
    status no longer allows cancelling.
    """
    if HotelBookingStatus.is_cancelled(booking.status):
        raise ValidationError(ALREADY_CANCELLED)
    if not HotelBookingStatus.can_be_cancelled(booking.status):
        raise ValidationError(CANNOT_BE_CANCELLED)

    with transaction.atomic():
        booking.status = HotelBookingStatus.CANCELLED
        booking.save(update_fields=["status", "updated_at"])
        HotelAvailability.objects.filter(pk=booking.availability_id).update(
            rooms_available=F("rooms_available") + 1
        )

    return booking
