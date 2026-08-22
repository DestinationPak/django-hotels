"""HotelViewSet's django-filter query params: city, status, owner."""

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from django_hotels.choices import HotelStatus
from django_hotels.tests.factories import HotelFactory, HotelOwnerFactory


class HotelViewSetFilteringTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse("hotels-api:hotel-list")

    def test_filters_by_city(self):
        matching = HotelFactory(city="Hunza")
        HotelFactory(city="Skardu")

        response = self.client.get(self.url, {"city": "Hunza"})

        self.assertEqual([h["slug"] for h in response.data], [matching.slug])

    def test_filters_by_status(self):
        draft = HotelFactory(status=HotelStatus.DRAFT)
        HotelFactory(status=HotelStatus.PUBLISHED)

        response = self.client.get(self.url, {"status": HotelStatus.DRAFT})

        self.assertEqual([h["slug"] for h in response.data], [draft.slug])

    def test_filters_by_owner(self):
        owner = HotelOwnerFactory()
        matching = HotelFactory(owner=owner)
        HotelFactory()

        response = self.client.get(self.url, {"owner": owner.id})

        self.assertEqual([h["slug"] for h in response.data], [matching.slug])
