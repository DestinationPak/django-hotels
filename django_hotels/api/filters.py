"""FilterSets for django_hotels' public API."""

import django_filters

from django_hotels.models import Hotel, HotelAvailability


class HotelAvailabilityFilter(django_filters.FilterSet):
    """Filters availability search by hotel, room type, and date range."""

    hotel = django_filters.CharFilter(field_name="room_type__hotel__slug")
    room_type = django_filters.NumberFilter(field_name="room_type_id")
    date_from = django_filters.DateFilter(field_name="date", lookup_expr="gte")
    date_to = django_filters.DateFilter(field_name="date", lookup_expr="lte")

    class Meta:
        model = HotelAvailability
        fields = ["hotel", "room_type", "date_from", "date_to"]


class HotelFilter(django_filters.FilterSet):
    city = django_filters.CharFilter(field_name="location__name", lookup_expr="iexact")

    class Meta:
        model = Hotel
        fields = ["city", "status", "owner"]
