"""
DRF API for django-hotels, deprecated and removed in 1.0.0.

From 1.0.0 the package ships the domain only: models, querysets and
`django_hotels.services`. Build your own API on those instead.
"""

import warnings

warnings.warn(
    "django_hotels.api is deprecated and will be removed in django-hotels 1.0.0. "
    "Build your own API on django_hotels.services and the model querysets.",
    DeprecationWarning,
    stacklevel=2,
)
