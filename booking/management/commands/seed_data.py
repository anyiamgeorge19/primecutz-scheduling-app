import datetime

from django.core.management.base import BaseCommand

from booking.models import Barber, Service


class Command(BaseCommand):
    help = "Seed the database with sample PrimeCutz barbers and services."

    def handle(self, *args, **options):
        services = [
            {"name": "Classic Haircut", "duration_minutes": 30, "price": 3500,
             "description": "A sharp, timeless cut tailored to your style."},
            {"name": "Skin Fade", "duration_minutes": 45, "price": 4500,
             "description": "Clean, blended fade from skin to top."},
            {"name": "Beard Trim", "duration_minutes": 20, "price": 2000,
             "description": "Shape-up and line-up for a crisp beard."},
            {"name": "Haircut + Beard Combo", "duration_minutes": 50, "price": 5500,
             "description": "The full package — cut and beard, done right."},
            {"name": "Kids Haircut", "duration_minutes": 25, "price": 2500,
             "description": "Patient, friendly cuts for the little ones."},
        ]

        for s in services:
            obj, created = Service.objects.get_or_create(name=s["name"], defaults=s)
            self.stdout.write(self.style.SUCCESS(f"{'Created' if created else 'Exists'}: {obj.name}"))

        barbers = [
            {"name": "Emeka \"The Blade\" Obi", "bio": "12 years of precision fades and sharp lines.",
             "work_start": datetime.time(9, 0), "work_end": datetime.time(19, 0), "days_off": "6"},
            {"name": "Tunde Adewale", "bio": "Specialist in classic cuts and beard sculpting.",
             "work_start": datetime.time(10, 0), "work_end": datetime.time(18, 0), "days_off": "0"},
            {"name": "David Okon", "bio": "Modern styles, quick turnarounds, great vibes.",
             "work_start": datetime.time(9, 0), "work_end": datetime.time(17, 0), "days_off": "6"},
        ]

        for b in barbers:
            obj, created = Barber.objects.get_or_create(name=b["name"], defaults=b)
            self.stdout.write(self.style.SUCCESS(f"{'Created' if created else 'Exists'}: {obj.name}"))

        self.stdout.write(self.style.SUCCESS("Seeding complete."))
