from django.db import models


class ActiveQuerySet(models.QuerySet):
    def active(self):
        return self.filter(is_active=True)


class HotelOwnerQuerySet(ActiveQuerySet):
    def active(self):
        return super().active().filter(verified=True)


class HotelQuerySet(ActiveQuerySet):
    def active(self):
        return super().active().filter(owner__verified=True)


class HotelAvailabilityQuerySet(models.QuerySet):
    def bookable(self):
        """
        Availability a guest can book, earliest date first.

        Leaves out sold-out dates, inactive room types, and hotels that are
        inactive or whose owner isn't verified (the `Hotel.objects.active()`
        rules).
        """
        return self.filter(
            rooms_available__gt=0,
            room_type__is_active=True,
            room_type__hotel__is_active=True,
            room_type__hotel__owner__verified=True,
        ).order_by("date")


class HotelBookingQuerySet(models.QuerySet):
    def matching_guest(self, number, *, otp=None, email=None):
        """
        The booking a guest proves they own, by `number` plus `otp` or `email`.

        Never matches on `number` alone, so a guessed or leaked reference
        number can't pull up someone else's booking. Empty when neither
        `otp` nor `email` is given; `email` matches case-insensitively.
        """
        if otp:
            return self.filter(number=number, otp=otp)
        if email:
            return self.filter(number=number, email__iexact=email)
        return self.none()
