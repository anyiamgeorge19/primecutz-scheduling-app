import datetime

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from .models import Appointment, Barber, Service


def next_weekday(target_weekday):
    """Return the next date matching the given weekday (0=Mon...6=Sun) that's in the future."""
    today = datetime.date.today()
    days_ahead = (target_weekday - today.weekday()) % 7
    days_ahead = days_ahead or 7  # always strictly in the future
    return today + datetime.timedelta(days=days_ahead)


class BookingModelTests(TestCase):
    def setUp(self):
        self.barber = Barber.objects.create(
            name="Test Barber",
            work_start=datetime.time(9, 0),
            work_end=datetime.time(17, 0),
            days_off="6",  # Sunday off
        )
        self.service = Service.objects.create(name="Haircut", duration_minutes=30, price=3000)
        self.monday = next_weekday(0)
        self.sunday = next_weekday(6)

    def test_end_time_auto_calculated(self):
        appt = Appointment.objects.create(
            client_name="Jane", client_email="jane@test.com", client_phone="080",
            barber=self.barber, service=self.service,
            date=self.monday, start_time=datetime.time(10, 0),
        )
        self.assertEqual(appt.end_time, datetime.time(10, 30))

    def test_rejects_double_booking_same_slot(self):
        Appointment.objects.create(
            client_name="Jane", client_email="jane@test.com", client_phone="080",
            barber=self.barber, service=self.service,
            date=self.monday, start_time=datetime.time(10, 0),
        )
        clashing = Appointment(
            client_name="John", client_email="john@test.com", client_phone="081",
            barber=self.barber, service=self.service,
            date=self.monday, start_time=datetime.time(10, 15),
        )
        with self.assertRaises(ValidationError):
            clashing.clean()

    def test_rejects_booking_outside_working_hours(self):
        appt = Appointment(
            client_name="Late Client", client_email="l@test.com", client_phone="082",
            barber=self.barber, service=self.service,
            date=self.monday, start_time=datetime.time(16, 45),  # would end at 17:15, past close
        )
        with self.assertRaises(ValidationError):
            appt.clean()

    def test_rejects_booking_on_day_off(self):
        appt = Appointment(
            client_name="Sunday Client", client_email="s@test.com", client_phone="083",
            barber=self.barber, service=self.service,
            date=self.sunday, start_time=datetime.time(10, 0),
        )
        with self.assertRaises(ValidationError):
            appt.clean()

    def test_allows_back_to_back_non_overlapping_bookings(self):
        Appointment.objects.create(
            client_name="Jane", client_email="jane@test.com", client_phone="080",
            barber=self.barber, service=self.service,
            date=self.monday, start_time=datetime.time(10, 0),
        )
        # Starts exactly when the first one ends — should be fine.
        back_to_back = Appointment(
            client_name="John", client_email="john@test.com", client_phone="081",
            barber=self.barber, service=self.service,
            date=self.monday, start_time=datetime.time(10, 30),
        )
        back_to_back.clean()  # should not raise


class BookingViewTests(TestCase):
    def setUp(self):
        self.barber = Barber.objects.create(name="Test Barber")
        self.service = Service.objects.create(name="Haircut", duration_minutes=30, price=3000)
        self.monday = next_weekday(0)

    def test_home_page_loads(self):
        response = self.client.get(reverse("booking:home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "PrimeCutz")

    def test_booking_form_creates_appointment(self):
        response = self.client.post(reverse("booking:book_appointment"), {
            "client_name": "Jane Doe",
            "client_email": "jane@test.com",
            "client_phone": "08012345678",
            "barber": self.barber.pk,
            "service": self.service.pk,
            "date": self.monday.isoformat(),
            "start_time": "10:00",
            "notes": "",
        })
        self.assertEqual(Appointment.objects.count(), 1)
        self.assertEqual(response.status_code, 302)

    def test_available_slots_endpoint_returns_json(self):
        url = reverse("booking:available_slots")
        response = self.client.get(url, {
            "barber_id": self.barber.pk,
            "service_id": self.service.pk,
            "date": self.monday.isoformat(),
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn("slots", response.json())
        self.assertTrue(len(response.json()["slots"]) > 0)

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse("booking:dashboard"))
        self.assertEqual(response.status_code, 302)  # redirected to login
