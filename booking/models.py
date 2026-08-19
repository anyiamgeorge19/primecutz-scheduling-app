import datetime

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse


class Barber(models.Model):
    """A staff member who performs haircuts / grooming services."""

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, null=True, blank=True,
        help_text="Optional: link to a login account for this barber."
    )
    name = models.CharField(max_length=100)
    bio = models.TextField(blank=True)
    photo = models.ImageField(upload_to="barbers/", blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True)
    is_active = models.BooleanField(default=True)

    # Working hours (simple daily model — same hours every working day)
    work_start = models.TimeField(default=datetime.time(9, 0))
    work_end = models.TimeField(default=datetime.time(18, 0))

    # Days off, e.g. "0,6" for Monday & Sunday (0=Mon ... 6=Sun)
    days_off = models.CharField(
        max_length=20, default="6",
        help_text="Comma-separated weekday numbers off (0=Mon ... 6=Sun). Default: Sunday."
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def days_off_list(self):
        return [int(d) for d in self.days_off.split(",") if d.strip() != ""]


class Service(models.Model):
    """A service PrimeCutz offers, e.g. Haircut, Beard Trim, Fade."""

    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    duration_minutes = models.PositiveIntegerField(default=30)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.duration_minutes} min - ₦{self.price})"


class Appointment(models.Model):
    """A single booked slot: one client, one barber, one service, one time."""

    STATUS_PENDING = "pending"
    STATUS_CONFIRMED = "confirmed"
    STATUS_CANCELLED = "cancelled"
    STATUS_COMPLETED = "completed"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_CONFIRMED, "Confirmed"),
        (STATUS_CANCELLED, "Cancelled"),
        (STATUS_COMPLETED, "Completed"),
    ]

    client_name = models.CharField(max_length=100)
    client_email = models.EmailField()
    client_phone = models.CharField(max_length=20)

    barber = models.ForeignKey(Barber, on_delete=models.CASCADE, related_name="appointments")
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name="appointments")

    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField(editable=False)

    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default=STATUS_PENDING)
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["date", "start_time"]
        constraints = [
            models.UniqueConstraint(
                fields=["barber", "date", "start_time"],
                name="unique_barber_slot",
            )
        ]

    def __str__(self):
        return f"{self.client_name} with {self.barber.name} on {self.date} at {self.start_time}"

    def get_absolute_url(self):
        return reverse("booking:appointment_detail", args=[self.pk])

    def save(self, *args, **kwargs):
        # Auto-calculate end_time from the service duration
        start_dt = datetime.datetime.combine(self.date, self.start_time)
        end_dt = start_dt + datetime.timedelta(minutes=self.service.duration_minutes)
        self.end_time = end_dt.time()
        super().save(*args, **kwargs)

    def clean(self):
        errors = {}

        if self.date and self.date < datetime.date.today():
            errors["date"] = "You cannot book an appointment in the past."

        if self.barber_id and self.date:
            if self.date.weekday() in self.barber.days_off_list():
                errors["date"] = f"{self.barber.name} is off on that day. Please pick another date."

        if self.barber_id and self.start_time and self.service_id:
            start_dt = datetime.datetime.combine(self.date or datetime.date.today(), self.start_time)
            end_dt = start_dt + datetime.timedelta(minutes=self.service.duration_minutes)

            if self.start_time < self.barber.work_start or end_dt.time() > self.barber.work_end:
                errors["start_time"] = (
                    f"{self.barber.name} works between {self.barber.work_start.strftime('%I:%M %p')} "
                    f"and {self.barber.work_end.strftime('%I:%M %p')}. Choose a time that fits."
                )

            # Overlap check against existing (non-cancelled) appointments for this barber/date
            overlapping = Appointment.objects.filter(
                barber=self.barber, date=self.date
            ).exclude(status=self.STATUS_CANCELLED).exclude(pk=self.pk)

            for appt in overlapping:
                if self.start_time < appt.end_time and end_dt.time() > appt.start_time:
                    errors["start_time"] = (
                        f"{self.barber.name} already has a booking from "
                        f"{appt.start_time.strftime('%I:%M %p')} to {appt.end_time.strftime('%I:%M %p')} "
                        "on that date. Please choose another time."
                    )
                    break

        if errors:
            raise ValidationError(errors)
