from django.test import TestCase
from django.urls import reverse

from django_hotels.admin import REOPEN_NOT_ALLOWED
from django_hotels.choices import HotelBookingStatus
from django_hotels.models import HotelBooking
from django_hotels.tests.factories import HotelBookingFactory, UserFactory


def admin_form_data(form):
    """The POST data a browser would send for an unchanged admin form."""
    data = {}
    for name in form.fields:
        bound = form[name]
        value = bound.value()
        widget = bound.field.widget
        if hasattr(widget, "widgets") and hasattr(widget, "decompress"):
            parts = value if isinstance(value, (list, tuple)) else widget.decompress(value)
            for index, part in enumerate(parts):
                data[f"{name}_{index}"] = "" if part is None else part
        elif isinstance(value, bool):
            if value:
                data[name] = "on"
        elif isinstance(value, (list, tuple)):
            data[name] = [str(item) for item in value]
        else:
            data[name] = "" if value is None else value
    return data


class HotelBookingAdminTestCase(TestCase):
    """Cancelling, reopening and deleting a booking in the admin keep rooms in step."""

    def setUp(self):
        super().setUp()
        self.client.force_login(UserFactory(is_staff=True, is_superuser=True))
        self.booking = HotelBookingFactory(
            availability__rooms_available=4, status=HotelBookingStatus.CONFIRMED
        )
        self.availability = self.booking.availability
        self.change_url = reverse("admin:django_hotels_hotelbooking_change", args=[self.booking.pk])

    def post_status(self, status):
        form = self.client.get(self.change_url).context["adminform"].form
        return self.client.post(self.change_url, {**admin_form_data(form), "status": status})

    def rooms_available(self):
        self.availability.refresh_from_db()
        return self.availability.rooms_available

    def test_cancelling_gives_the_room_back(self):
        response = self.post_status(HotelBookingStatus.CANCELLED)

        self.assertEqual(response.status_code, 302)
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, HotelBookingStatus.CANCELLED)
        self.assertEqual(self.rooms_available(), 5)

    def test_saving_without_a_status_change_leaves_rooms_alone(self):
        self.post_status(HotelBookingStatus.CONFIRMED)

        self.assertEqual(self.rooms_available(), 4)

    def test_a_cancelled_booking_cannot_be_reopened(self):
        self.post_status(HotelBookingStatus.CANCELLED)

        response = self.post_status(HotelBookingStatus.PENDING)

        self.assertEqual(response.status_code, 200)
        self.assertIn(REOPEN_NOT_ALLOWED, response.context["adminform"].form.errors["status"])
        self.assertEqual(self.rooms_available(), 5)

    def test_the_availability_is_read_only_once_the_booking_exists(self):
        form = self.client.get(self.change_url).context["adminform"].form

        self.assertNotIn("availability", form.fields)

    def test_deleting_a_live_booking_gives_the_room_back(self):
        delete_url = reverse("admin:django_hotels_hotelbooking_delete", args=[self.booking.pk])

        self.client.post(delete_url, {"post": "yes"})

        self.assertFalse(HotelBooking.objects.filter(pk=self.booking.pk).exists())
        self.assertEqual(self.rooms_available(), 5)

    def test_bulk_delete_skips_cancelled_bookings(self):
        cancelled = HotelBookingFactory(availability=self.availability, status=HotelBookingStatus.CANCELLED)

        self.client.post(
            reverse("admin:django_hotels_hotelbooking_changelist"),
            {"action": "delete_selected", "_selected_action": [self.booking.pk, cancelled.pk], "post": "yes"},
        )

        self.assertFalse(HotelBooking.objects.exists())
        self.assertEqual(self.rooms_available(), 5)
