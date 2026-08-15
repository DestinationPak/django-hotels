from django.contrib import admin

from django_hotels.models import (
    Hotel,
    HotelAvailability,
    HotelBooking,
    HotelImage,
    HotelOwner,
    HotelRoomType,
)


@admin.register(HotelOwner)
class HotelOwnerAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "verified", "is_active")
    search_fields = ("name", "email")


@admin.register(Hotel)
class HotelAdmin(admin.ModelAdmin):
    list_display = ("name", "owner", "city", "status", "is_active")
    list_filter = ("status", "is_active", "city")
    search_fields = ("name", "city")


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
