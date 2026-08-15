from django.db import models


class HotelStatus(models.TextChoices):
    """
    Editorial state of a Hotel, independent of `is_active` (which is
    soft-delete/visibility, not workflow).
    """

    DRAFT = "DRAFT", "Draft"
    PUBLISHED = "PUBLISHED", "Published"


class HotelBookingStatus(models.TextChoices):
    """Lifecycle states of a booking - mirrors django_trips.choices.BookingStatus."""

    PENDING = "PENDING", "Pending"
    WAITING_PAYMENT = "WAITING_PAYMENT", "Awaiting Payment"
    CONFIRMED = "CONFIRMED", "Confirmed"
    PARTIAL_PAYMENT = "PARTIAL_PAYMENT", "Partial Payment"
    COMPLETED = "COMPLETED", "Completed"
    CANCELLED = "CANCELLED", "Cancelled"

    @classmethod
    def is_cancelled(cls, status):
        return status == cls.CANCELLED

    @classmethod
    def can_be_cancelled(cls, status):
        return status in (cls.PENDING, cls.WAITING_PAYMENT)
