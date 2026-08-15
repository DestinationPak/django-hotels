import random
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.text import slugify
from faker import Faker

from django_hotels.models import Hotel, HotelAvailability, HotelOwner, HotelRoomType

fake = Faker()
User = get_user_model()

CITIES = ("Hunza", "Skardu", "Naran", "Murree", "Fairy Meadows")
ROOM_TYPES = (("Standard Double", 8000, 2), ("Deluxe Suite", 15000, 4))


class Command(BaseCommand):
    """
    Generate a batch of hotels with random demo data.

    EXAMPLE USAGE:
        ./manage.py generate_hotels --batch_size=10
    """

    help = "Generate batches of hotels with pre-populated random data"

    def add_arguments(self, parser):
        parser.add_argument("--batch_size", type=int, default=10, dest="batch_size")

    def handle(self, *args, **options):
        batch_size = options["batch_size"]
        user, _ = User.objects.get_or_create(
            username="hotels-seed-bot", defaults={"email": "seed@example.com"}
        )

        for _ in range(batch_size):
            owner_name = fake.company()
            owner = HotelOwner.objects.create(
                name=owner_name,
                slug=f"{slugify(owner_name)}-{random.randint(1000, 9999)}",
                email=fake.company_email(),
                verified=True,
            )
            hotel_name = f"{fake.city()} {random.choice(['Inn', 'Resort', 'Lodge'])}"
            hotel = Hotel.objects.create(
                name=hotel_name,
                slug=f"{slugify(hotel_name)}-{random.randint(1000, 9999)}",
                owner=owner,
                city=random.choice(CITIES),
                description=fake.paragraph(),
                created_by=user,
            )
            for room_name, price, occupancy in ROOM_TYPES:
                room_type = HotelRoomType.objects.create(
                    hotel=hotel,
                    name=room_name,
                    base_price=price,
                    max_occupancy=occupancy,
                )
                for day in range(7):
                    HotelAvailability.objects.create(
                        room_type=room_type,
                        date=timezone.now().date() + timedelta(days=day),
                        rooms_available=random.randint(1, 5),
                    )

        self.stdout.write(self.style.SUCCESS(f"Generated {batch_size} hotels"))
