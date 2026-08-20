"""
The schema/swagger-ui/redoc views are scoped to this app's own urlconf
(django_hotels.api.urls), not the host project's ROOT_URLCONF - see the
comment in api/urls.py. Mirrors django_trips' equivalent scoping.
"""

import pytest
from django.urls import reverse
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_schema_is_scoped_to_the_hotels_api_and_self_identifying():
    response = APIClient().get(reverse("hotels-api:schema"))

    assert response.status_code == 200
    assert response.data["info"]["title"] == "Django Hotels API"
    paths = response.data["paths"]
    assert any("/hotels/" in path for path in paths)
    assert not any("/trips/" in path for path in paths)


@pytest.mark.django_db
def test_swagger_ui_is_reachable():
    response = APIClient().get(reverse("hotels-api:swagger-ui"))
    assert response.status_code == 200


@pytest.mark.django_db
def test_redoc_is_reachable():
    response = APIClient().get(reverse("hotels-api:redoc"))
    assert response.status_code == 200
