import swapper
from django import forms
from django.contrib import admin

from django_hotels.choices import HotelBookingStatus
from django_hotels.models import (
    Hotel,
    HotelAvailability,
    HotelBooking,
    HotelImage,
    HotelOwner,
    HotelRoomType,
    Location,
)
from django_hotels.services import cancel_hotel_booking, delete_hotel_booking


@admin.register(HotelOwner)
class HotelOwnerAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "verified", "is_active")
    search_fields = ("name", "email")


@admin.register(Hotel)
class HotelAdmin(admin.ModelAdmin):
    list_display = ("name", "owner", "location", "status", "is_active")
    list_filter = ("status", "is_active")
    search_fields = ("name", "location__name")


class LocationAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "lat", "lng")
    search_fields = ("name", "slug")


# Registering LocationAdmin against django_hotels.Location only makes
# sense while it's actually the active model - once
# DJANGO_HOTELS_LOCATION_MODEL is swapped, this table/model isn't
# migrated at all.
if not swapper.is_swapped("django_hotels", "Location"):
    admin.site.register(Location, LocationAdmin)


@admin.register(HotelRoomType)
class HotelRoomTypeAdmin(admin.ModelAdmin):
    list_display = ("hotel", "name", "base_price", "max_occupancy", "is_active")


@admin.register(HotelAvailability)
class HotelAvailabilityAdmin(admin.ModelAdmin):
    list_display = ("room_type", "date", "effective_price", "rooms_available")
    list_filter = ("date",)


@admin.register(HotelImage)
class HotelImageAdmin(admin.ModelAdmin):
    list_display = ("hotel", "order")


REOPEN_NOT_ALLOWED = (
    "A cancelled booking can't be reopened, since its room may be taken by now. "
    "Create a new booking instead."
)


class HotelBookingAdminForm(forms.ModelForm):
    class Meta:
        model = HotelBooking
        fields = "__all__"

    def clean_status(self):
        status = self.cleaned_data["status"]
        if (
            self.instance.pk
            and HotelBookingStatus.is_cancelled(self.instance.status)
            and not HotelBookingStatus.is_cancelled(status)
        ):
            raise forms.ValidationError(REOPEN_NOT_ALLOWED)
        return status


@admin.register(HotelBooking)
class HotelBookingAdmin(admin.ModelAdmin):
    """
    Bookings, kept in step with their availability.

    Cancelling or deleting a booking here gives its room back, a cancelled
    booking can't be reopened, and the fields that decide what a booking
    holds are read-only once it exists.
    """

    form = HotelBookingAdminForm
    capacity_fields = ("availability",)
    list_display = ("number", "full_name", "email", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("number", "full_name", "email")

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = super().get_readonly_fields(request, obj)
        return (*readonly_fields, *self.capacity_fields) if obj else readonly_fields

    def save_model(self, request, obj, form, change):
        cancelling = (
            change and "status" in form.changed_data and HotelBookingStatus.is_cancelled(obj.status)
        )
        if cancelling:
            obj.status = form.initial["status"]
        super().save_model(request, obj, form, change)
        if cancelling:
            cancel_hotel_booking(obj, check_cancellable=False)

    def delete_model(self, request, obj):
        delete_hotel_booking(obj)

    def delete_queryset(self, request, queryset):
        for booking in queryset:
            delete_hotel_booking(booking)
