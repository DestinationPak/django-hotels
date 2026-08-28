from rest_framework import serializers

from django_hotels.location_adapter import get_location_adapter
from django_hotels.models import (
    Hotel,
    HotelAvailability,
    HotelBooking,
    HotelImage,
    HotelOwner,
    HotelRoomType,
)


class HotelOwnerSerializer(serializers.ModelSerializer):
    class Meta:
        model = HotelOwner
        fields = (
            "id",
            "name",
            "slug",
            "description",
            "email",
            "mobile",
            "verified",
        )


class HotelImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = HotelImage
        fields = ("id", "image", "caption", "order")


class HotelRoomTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = HotelRoomType
        fields = ("id", "name", "base_price", "max_occupancy")


class LocationSerializer(serializers.Serializer):
    name = serializers.SerializerMethodField()
    slug = serializers.SerializerMethodField()
    lat = serializers.SerializerMethodField()
    lng = serializers.SerializerMethodField()

    def get_name(self, obj) -> str | None:
        return get_location_adapter().get_name(obj)

    def get_slug(self, obj) -> str | None:
        return get_location_adapter().get_slug(obj)

    def get_lat(self, obj) -> float | None:
        return get_location_adapter().get_lat(obj)

    def get_lng(self, obj) -> float | None:
        return get_location_adapter().get_lng(obj)


class HotelListSerializer(serializers.ModelSerializer):
    owner = HotelOwnerSerializer(read_only=True)
    location = LocationSerializer(read_only=True, allow_null=True)

    class Meta:
        model = Hotel
        fields = ("id", "name", "slug", "owner", "location", "status")


class HotelDetailSerializer(serializers.ModelSerializer):
    owner = HotelOwnerSerializer(read_only=True)
    location = LocationSerializer(read_only=True, allow_null=True)
    images = HotelImageSerializer(many=True, read_only=True)
    room_types = HotelRoomTypeSerializer(many=True, read_only=True)

    class Meta:
        model = Hotel
        fields = (
            "id",
            "name",
            "slug",
            "owner",
            "location",
            "description",
            "status",
            "images",
            "room_types",
        )


class HotelAvailabilityRoomTypeSerializer(serializers.ModelSerializer):
    """Minimal hotel/room context for an availability-search row."""

    hotel = serializers.SlugRelatedField(slug_field="slug", read_only=True)

    class Meta:
        model = HotelRoomType
        fields = ("id", "name", "hotel")


class HotelAvailabilitySerializer(serializers.ModelSerializer):
    room_type = HotelAvailabilityRoomTypeSerializer(read_only=True)

    class Meta:
        model = HotelAvailability
        fields = ("id", "room_type", "date", "effective_price", "rooms_available")


class HotelBookingCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = HotelBooking
        fields = (
            "id",
            "number",
            "availability",
            "full_name",
            "email",
            "phone_number",
            "guests",
            "message",
            "total_price",
        )
        read_only_fields = ("id", "number", "total_price")

    def create(self, validated_data):
        availability = validated_data["availability"]
        guests = validated_data.get("guests", 1)
        validated_data["total_price"] = availability.effective_price * guests
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            validated_data["created_by"] = request.user
        return super().create(validated_data)


class HotelBookingLookupSerializer(serializers.ModelSerializer):
    class Meta:
        model = HotelBooking
        fields = (
            "number",
            "full_name",
            "email",
            "guests",
            "status",
            "total_price",
            "created_at",
        )
