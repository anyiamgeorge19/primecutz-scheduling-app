import datetime
import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from .forms import AppointmentForm, AppointmentStatusForm
from .models import Appointment, Barber, Service


def home(request):
    services = Service.objects.filter(is_active=True)
    barbers = Barber.objects.filter(is_active=True)
    return render(request, "booking/home.html", {"services": services, "barbers": barbers})


def book_appointment(request):
    if request.method == "POST":
        form = AppointmentForm(request.POST)
        if form.is_valid():
            appointment = form.save(commit=False)
            try:
                appointment.full_clean()
            except ValidationError:
                pass  # already surfaced via form.clean(); this is a safety net
            appointment.save()
            messages.success(
                request,
                f"Thanks {appointment.client_name}! Your booking with "
                f"{appointment.barber.name} on {appointment.date} at "
                f"{appointment.start_time.strftime('%I:%M %p')} is {appointment.get_status_display().lower()}.",
            )
            return redirect("booking:appointment_detail", pk=appointment.pk)
    else:
        form = AppointmentForm()

    return render(request, "booking/book_appointment.html", {"form": form})


def appointment_detail(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk)
    return render(request, "booking/appointment_detail.html", {"appointment": appointment})


def get_available_slots(request):
    """AJAX endpoint: given a barber + date + service, return open time slots."""
    barber_id = request.GET.get("barber_id")
    service_id = request.GET.get("service_id")
    date_str = request.GET.get("date")

    if not (barber_id and service_id and date_str):
        return JsonResponse({"slots": []})

    try:
        barber = Barber.objects.get(pk=barber_id)
        service = Service.objects.get(pk=service_id)
        date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
    except (Barber.DoesNotExist, Service.DoesNotExist, ValueError):
        return JsonResponse({"slots": []})

    if date < datetime.date.today() or date.weekday() in barber.days_off_list():
        return JsonResponse({"slots": []})

    duration = datetime.timedelta(minutes=service.duration_minutes)
    step = datetime.timedelta(minutes=15)

    existing = list(
        Appointment.objects.filter(barber=barber, date=date)
        .exclude(status=Appointment.STATUS_CANCELLED)
        .values_list("start_time", "end_time")
    )

    slots = []
    current = datetime.datetime.combine(date, barber.work_start)
    end_of_day = datetime.datetime.combine(date, barber.work_end)
    now = datetime.datetime.now()

    while current + duration <= end_of_day:
        slot_start = current.time()
        slot_end = (current + duration).time()

        overlaps = any(slot_start < e and slot_end > s for s, e in existing)
        in_past = date == now.date() and current <= now

        if not overlaps and not in_past:
            slots.append(slot_start.strftime("%H:%M"))

        current += step

    return JsonResponse({"slots": slots})


@login_required
def dashboard(request):
    """Staff-only view of upcoming and past appointments."""
    status = request.GET.get("status", "")
    appointments = Appointment.objects.select_related("barber", "service").all()

    if status:
        appointments = appointments.filter(status=status)

    today = datetime.date.today()
    upcoming = appointments.filter(date__gte=today)
    past = appointments.filter(date__lt=today)

    return render(
        request,
        "booking/dashboard.html",
        {
            "upcoming": upcoming,
            "past": past,
            "status_choices": Appointment.STATUS_CHOICES,
            "selected_status": status,
        },
    )


@login_required
def update_status(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk)
    if request.method == "POST":
        form = AppointmentStatusForm(request.POST, instance=appointment)
        if form.is_valid():
            form.save()
            messages.success(request, f"Appointment #{appointment.pk} updated to {appointment.get_status_display()}.")
    return redirect("booking:dashboard")


@login_required
def cancel_appointment(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk)
    if request.method == "POST":
        appointment.status = Appointment.STATUS_CANCELLED
        appointment.save()
        messages.info(request, f"Appointment #{appointment.pk} was cancelled.")
    return redirect("booking:dashboard")
