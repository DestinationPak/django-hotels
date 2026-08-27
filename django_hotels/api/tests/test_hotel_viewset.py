"""
HotelViewSet is the public catalog - read-only, no exceptions.

Mirrors django_trips' TripViewSet hardening
(test_trip_write_methods_disabled.py): locks in that the public endpoint
never regains a write method - not "unauthorized", flatly absent - and
that anonymous and authenticated callers see the same unscoped catalog.
"""

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient

from django_hotels.models import Hotel, HotelOwner
from django_hotels.tests.factories import LocationFactory

User = get_user_model()


@pytest.fixture
def hotel(db):
    owner = HotelOwner.objects.create(name="Karakoram Stays", verified=True)
    creator = User.objects.create(username="staff")
    return Hotel.objects.create(
        name="Hunza Serena", owner=owner, location=LocationFactory(name="Hunza"), created_by=creator
    )


@pytest.fixture
def list_url():
    return reverse("hotels-api:hotel-list")


@pytest.fixture
def detail_url(hotel):
    return reverse("hotels-api:hotel-detail", kwargs={"slug": hotel.slug})


@pytest.mark.django_db
def test_create_not_allowed(list_url):
    response = APIClient().post(list_url, {})
    assert response.status_code == 405


@pytest.mark.django_db
def test_update_not_allowed(detail_url):
    response = APIClient().put(detail_url, {})
    assert response.status_code == 405


@pytest.mark.django_db
def test_delete_not_allowed(detail_url):
    response = APIClient().delete(detail_url)
    assert response.status_code == 405


@pytest.mark.django_db
def test_anonymous_and_authenticated_reads_return_the_same_unscoped_catalog(
    hotel, list_url
):
    other_user = User.objects.create(username="traveller")

    anonymous_response = APIClient().get(list_url)
    authenticated_client = APIClient()
    authenticated_client.force_authenticate(other_user)
    authenticated_response = authenticated_client.get(list_url)

    assert anonymous_response.status_code == 200
    assert authenticated_response.status_code == 200
    assert anonymous_response.data == authenticated_response.data
    assert [r["slug"] for r in anonymous_response.data] == [hotel.slug]
