from rest_framework import serializers

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


class HotelListSerializer(serializers.ModelSerializer):
    owner = HotelOwnerSerializer(read_only=True)

    class Meta:
        model = Hotel
        fields = ("id", "name", "slug", "owner", "city", "status")


class HotelDetailSerializer(serializers.ModelSerializer):
    owner = HotelOwnerSerializer(read_only=True)
    images = HotelImageSerializer(many=True, read_only=True)
    room_types = HotelRoomTypeSerializer(many=True, read_only=True)

    class Meta:
        model = Hotel
        fields = (
            "id",
            "name",
            "slug",
            "owner",
            "city",
            "description",
            "status",
            "images",
            "room_types",
        )


class HotelAvailabilityRoomTypeSerializer(serializers.ModelSerializer):
    """Minimal room-type context for an availability row - just enough to
    say which hotel/room a date+price belongs to."""

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
