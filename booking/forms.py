import datetime

from django import forms

from .models import Appointment, Barber, Service


class AppointmentForm(forms.ModelForm):
    date = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"})
    )
    start_time = forms.TimeField(
        widget=forms.TimeInput(attrs={"type": "time", "class": "form-control"})
    )

    class Meta:
        model = Appointment
        fields = [
            "client_name", "client_email", "client_phone",
            "barber", "service", "date", "start_time", "notes",
        ]
        widgets = {
            "client_name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Full name"}),
            "client_email": forms.EmailInput(attrs={"class": "form-control", "placeholder": "you@email.com"}),
            "client_phone": forms.TextInput(attrs={"class": "form-control", "placeholder": "080..."}),
            "barber": forms.Select(attrs={"class": "form-control"}),
            "service": forms.Select(attrs={"class": "form-control"}),
            "notes": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Any special request?"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["barber"].queryset = Barber.objects.filter(is_active=True)
        self.fields["service"].queryset = Service.objects.filter(is_active=True)

    def clean_date(self):
        date = self.cleaned_data["date"]
        if date < datetime.date.today():
            raise forms.ValidationError("You cannot book a date in the past.")
        return date

    def clean(self):
        cleaned_data = super().clean()
        # Build a temporary (unsaved) instance so we can reuse the model's
        # full validation logic (working hours, overlaps, days off) here too.
        barber = cleaned_data.get("barber")
        service = cleaned_data.get("service")
        date = cleaned_data.get("date")
        start_time = cleaned_data.get("start_time")

        if barber and service and date and start_time:
            instance = Appointment(
                barber=barber, service=service, date=date, start_time=start_time,
            )
            try:
                instance.clean()
            except forms.ValidationError as e:
                for field, messages in e.message_dict.items():
                    for message in messages:
                        self.add_error(field if field in self.fields else None, message)
        return cleaned_data


class AppointmentStatusForm(forms.ModelForm):
    """Used by staff to update the status of an appointment."""

    class Meta:
        model = Appointment
        fields = ["status"]
        widgets = {
            "status": forms.Select(attrs={"class": "form-control"}),
        }
