from django.contrib import admin

from .models import Appointment, Barber, Service


@admin.register(Barber)
class BarberAdmin(admin.ModelAdmin):
    list_display = ["name", "phone", "work_start", "work_end", "is_active"]
    list_filter = ["is_active"]
    search_fields = ["name"]


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ["name", "duration_minutes", "price", "is_active"]
    list_filter = ["is_active"]
    search_fields = ["name"]


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ["client_name", "barber", "service", "date", "start_time", "status"]
    list_filter = ["status", "barber", "date"]
    search_fields = ["client_name", "client_email", "client_phone"]
    date_hierarchy = "date"
    readonly_fields = ["end_time", "created_at", "updated_at"]
