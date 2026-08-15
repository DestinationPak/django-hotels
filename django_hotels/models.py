"""
Hotels domain model.

This package is deliberately tenancy-oblivious, the same way django-trips is:
it has no concept of which user may manage a HotelOwner. That membership/
permission layer belongs to whatever project installs this app, not here.
"""

import random

from django.conf import settings
from django.db import models
from django.utils.text import slugify

from django_hotels import managers
from django_hotels.choices import HotelBookingStatus, HotelStatus


class HotelOwner(models.Model):
    """The business/brand that owns and operates one or more Hotels."""

    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=280, unique=True, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    mobile = models.CharField(max_length=20, null=True, blank=True)
    cancellation_policy = models.JSONField(default=list, blank=True, null=True)
    refund_policy = models.JSONField(default=list, blank=True, null=True)

    verified = models.BooleanField(default=False)
    is_active = models.BooleanField(
        default=True,
        help_text="Deactivating an owner also hides all of their hotels from "
        "the public API.",
    )

    objects = managers.HotelOwnerQuerySet.as_manager()

    class Meta:
        ordering = ["name", "verified"]

    def __str__(self):
        return str(self.name)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Hotel(models.Model):
    """One bookable property (a hotel/guesthouse) owned by a HotelOwner."""

    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=280, unique=True, null=True, blank=True)
    owner = models.ForeignKey(
        HotelOwner, related_name="hotels", on_delete=models.CASCADE
    )
    city = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)

    status = models.CharField(
        max_length=20,
        choices=HotelStatus.choices,
        default=HotelStatus.PUBLISHED,
        help_text="Editorial state (draft/published) - independent of is_active.",
    )
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="hotels", on_delete=models.CASCADE
    )

    objects = managers.HotelQuerySet.as_manager()

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return str(self.name)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class HotelRoomType(models.Model):
    """A room category/tier offered by a Hotel (e.g. Standard Double)."""

    hotel = models.ForeignKey(
        Hotel, related_name="room_types", on_delete=models.CASCADE
    )
    name = models.CharField(max_length=100)
    base_price = models.DecimalField(max_digits=10, decimal_places=0)
    max_occupancy = models.PositiveIntegerField(default=2)
    is_active = models.BooleanField(default=True)

    objects = managers.ActiveQuerySet.as_manager()

    class Meta:
        ordering = ["base_price"]

    def __str__(self):
        return f"{self.hotel} - {self.name}"


class HotelAvailability(models.Model):
    """A specific dated, priced, bookable instance of a HotelRoomType."""

    room_type = models.ForeignKey(
        HotelRoomType, related_name="availabilities", on_delete=models.CASCADE
    )
    date = models.DateField()
    price = models.DecimalField(
        max_digits=10,
        decimal_places=0,
        null=True,
        blank=True,
        help_text="Overrides room_type.base_price for this date when set.",
    )
    rooms_available = models.PositiveIntegerField(default=1)

    class Meta:
        verbose_name_plural = "Hotel availabilities"
        ordering = ["date"]
        unique_together = ("room_type", "date")

    def __str__(self):
        return f"{self.room_type} - {self.date}"

    @property
    def effective_price(self):
        return self.price if self.price is not None else self.room_type.base_price


class HotelImage(models.Model):
    hotel = models.ForeignKey(Hotel, related_name="images", on_delete=models.CASCADE)
    image = models.URLField()
    caption = models.CharField(max_length=255, blank=True, null=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"{self.hotel} image #{self.order}"


class HotelBooking(models.Model):
    """A guest or logged-in traveller's booking against one HotelAvailability."""

    number = models.CharField(
        max_length=16,
        unique=True,
        editable=False,
        help_text="Auto-generated booking reference number",
    )
    otp = models.CharField(
        max_length=4,
        editable=False,
        help_text="Auto-generated 4-digit code, paired with `number` as an "
        "alternative to `number` + `email` for the guest booking lookup.",
    )
    availability = models.ForeignKey(
        HotelAvailability, related_name="bookings", on_delete=models.CASCADE
    )

    full_name = models.CharField(max_length=255)
    email = models.EmailField()
    phone_number = models.CharField(max_length=30)
    guests = models.PositiveIntegerField(default=1)

    status = models.CharField(
        max_length=20,
        choices=HotelBookingStatus.choices,
        default=HotelBookingStatus.PENDING,
    )
    message = models.TextField(null=True, blank=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=0, default=0)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        related_name="hotel_bookings",
        on_delete=models.CASCADE,
        help_text="User who created this booking (null for guest bookings)",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [models.Index(fields=["status"])]

    def __str__(self):
        return f"<HotelBooking {self.full_name}, {self.status}>"

    def save(self, *args, **kwargs):
        if not self.number:
            self.number = self.generate_booking_number()
        if not self.otp:
            self.otp = self.generate_otp()
        super().save(*args, **kwargs)

    @classmethod
    def generate_booking_number(cls):
        """
        DPH000123
        DPH000284
        """
        prefix = "DPH"
        count = cls.objects.count() + 1
        padded_number = f"{count:06d}"
        suffix = f"{random.randint(0, 99):02d}"
        return f"{prefix}{padded_number}{suffix}"

    @classmethod
    def generate_otp(cls):
        """A random 4-digit code, not checked for uniqueness - it's only
        ever looked up together with `number`, which is unique."""
        return f"{random.randint(0, 9999):04d}"
