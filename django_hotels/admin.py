import swapper
from django.contrib import admin

from django_hotels.models import (
    Hotel,
    HotelAvailability,
    HotelBooking,
    HotelImage,
    HotelOwner,
    HotelRoomType,
    Location,
)


@admin.register(HotelOwner)
class HotelOwnerAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "verified", "is_active")
    search_fields = ("name", "email")


@admin.register(Hotel)
class HotelAdmin(admin.ModelAdmin):
    list_display = ("name", "owner", "location", "status", "is_active")
    list_filter = ("status", "is_active")
    search_fields = ("name",)


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


@admin.register(HotelBooking)
class HotelBookingAdmin(admin.ModelAdmin):
    list_display = ("number", "full_name", "email", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("number", "full_name", "email")
