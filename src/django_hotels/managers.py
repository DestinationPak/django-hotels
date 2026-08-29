from django.db import models


class ActiveQuerySet(models.QuerySet):
    def active(self):
        return self.filter(is_active=True)


class HotelOwnerQuerySet(ActiveQuerySet):
    def active(self):
        return super().active().filter(verified=True)


class HotelQuerySet(ActiveQuerySet):
    def active(self):
        return super().active().filter(owner__verified=True)
