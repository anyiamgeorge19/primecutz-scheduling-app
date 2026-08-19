from django.urls import path

from . import views

app_name = "booking"

urlpatterns = [
    path("", views.home, name="home"),
    path("book/", views.book_appointment, name="book_appointment"),
    path("appointment/<int:pk>/", views.appointment_detail, name="appointment_detail"),
    path("api/available-slots/", views.get_available_slots, name="available_slots"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("dashboard/appointment/<int:pk>/status/", views.update_status, name="update_status"),
    path("dashboard/appointment/<int:pk>/cancel/", views.cancel_appointment, name="cancel_appointment"),
]
