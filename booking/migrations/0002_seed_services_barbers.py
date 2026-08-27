import requests
from django.core.files.base import ContentFile
from django.db import migrations


SERVICES = [
    {"name": "Men's Haircut", "description": "Classic precision cut, tailored to your style.", "duration_minutes": 30, "price": 3500},
    {"name": "Beard Trim & Shape-Up", "description": "Clean lineup and beard shaping.", "duration_minutes": 20, "price": 2000},
    {"name": "Hair Coloring", "description": "Full or partial color, professional finish.", "duration_minutes": 60, "price": 8000},
    {"name": "Braiding", "description": "Neat, long-lasting braid styles.", "duration_minutes": 90, "price": 10000},
    {"name": "Kids' Haircut", "description": "Gentle, quick cuts for children.", "duration_minutes": 25, "price": 2500},
]

BARBERS = [
    {
        "name": "Emeka Johnson",
        "bio": "Specialist in fades and classic cuts, 6+ years experience.",
        "photo_url": "https://images.unsplash.com/photo-1634480257305-7f4ca3582e6a?auto=format&fit=crop&w=600&q=80",
    },
    {
        "name": "David Okafor",
        "bio": "Beard grooming expert with a sharp eye for detail.",
        "photo_url": "https://images.unsplash.com/photo-1672642150228-3fcd5826ec26?auto=format&fit=crop&w=600&q=80",
    },
    {
        "name": "Michael Adeyemi",
        "bio": "Known for clean lineups and braid styling.",
        "photo_url": "https://images.unsplash.com/photo-1494873446894-adbfecfc407a?auto=format&fit=crop&w=600&q=80",
    },
]


def seed_data(apps, schema_editor):
    Service = apps.get_model("booking", "Service")
    Barber = apps.get_model("booking", "Barber")

    for s in SERVICES:
        Service.objects.get_or_create(name=s["name"], defaults=s)

    for b in BARBERS:
        if Barber.objects.filter(name=b["name"]).exists():
            continue

        barber = Barber(name=b["name"], bio=b["bio"])

        try:
            response = requests.get(b["photo_url"], timeout=10)
            if response.status_code == 200:
                filename = f"{b['name'].replace(' ', '_').lower()}.jpg"
                barber.photo.save(filename, ContentFile(response.content), save=False)
        except requests.RequestException:
            pass

        barber.save()


def remove_data(apps, schema_editor):
    Service = apps.get_model("booking", "Service")
    Barber = apps.get_model("booking", "Barber")
    Service.objects.filter(name__in=[s["name"] for s in SERVICES]).delete()
    Barber.objects.filter(name__in=[b["name"] for b in BARBERS]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("booking", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_data, remove_data),
    ]
