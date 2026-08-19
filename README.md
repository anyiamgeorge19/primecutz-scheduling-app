# PrimeCutz — Personal Scheduling Web Application
**SEN 310 Assignment — Django Web Application**
Business: **PrimeCutz Barbershop**

A full booking/scheduling system that lets customers book haircut appointments
online, and lets barbershop staff manage those bookings from a dashboard.

---

## 1. Problem Statement

PrimeCutz currently takes bookings over the phone or WhatsApp, which leads to
double-bookings, missed messages, and no single source of truth for who is
booked when. This application solves that by giving:

- **Customers** a self-service page to pick a barber, a service, and an open
  time slot — with the system automatically preventing double-bookings and
  bookings outside working hours.
- **Staff** a login-protected dashboard to view, confirm, complete, or cancel
  appointments.

## 2. Tech Stack

| Layer        | Technology                                  |
|--------------|----------------------------------------------|
| Language     | Python 3.12                                   |
| Framework    | Django 6.1                                    |
| Database     | SQLite (dev) — swappable to PostgreSQL/MySQL for production |
| Frontend     | Django Templates, vanilla CSS, vanilla JS (fetch API for AJAX slot loading) |
| Auth         | Django's built-in auth system (staff/admin login) |

## 3. Data Model (ERD summary)

```
Barber                    Service                    Appointment
------                    -------                    -----------
id (PK)                   id (PK)                    id (PK)
name                       name                        client_name
bio                        description                 client_email
photo                      duration_minutes            client_phone
phone                      price                        barber_id (FK -> Barber)
work_start                 is_active                    service_id (FK -> Service)
work_end                                                date
days_off                                                start_time
is_active                                               end_time (auto-computed)
                                                          status (pending/confirmed/
                                                                  cancelled/completed)
                                                          notes
                                                          created_at / updated_at
```

**Relationships**
- One `Barber` → many `Appointment`s
- One `Service` → many `Appointment`s
- `Appointment` has a **unique constraint** on `(barber, date, start_time)` and
  a **model-level `clean()`** method that additionally rejects:
  - bookings in the past
  - bookings on a barber's day off
  - bookings outside the barber's working hours
  - bookings that **overlap** any existing (non-cancelled) appointment for
    that barber, based on service duration

This overlap logic is the core scheduling algorithm: it converts `start_time`
+ `service.duration_minutes` into an `end_time`, then checks
`new.start < existing.end AND new.end > existing.start` for every existing
appointment on that barber/date.

## 4. Key Features

- **Public booking flow** (`/book/`): customer picks barber → service → date,
  and the page calls a JSON endpoint (`/api/available-slots/`) via `fetch()`
  to show only real, open 15-minute-stepped slots for that combination —
  no server round-trip needed to see what's free.
- **Server-side validation** is enforced independently of the JS (via
  `Appointment.clean()` and `AppointmentForm.clean()`), so the system can't be
  double-booked even if someone bypasses the UI.
- **Booking confirmation page** with all appointment details.
- **Staff dashboard** (`/dashboard/`, login required): upcoming/past
  appointments, status filter, inline status updates, and cancellation.
- **Django Admin** (`/admin/`) for full CRUD on barbers, services, and
  appointments.
- **Automated tests** (`booking/tests.py`) covering the scheduling rules and
  core views — 9 tests, all passing.
- **Seed command** (`seed_data`) to populate demo barbers/services in one line.

## 5. Project Structure

```
primecutz_project/
├── manage.py
├── requirements.txt
├── primecutz/              # project config
│   ├── settings.py
│   ├── urls.py
├── booking/                 # the scheduling app
│   ├── models.py            # Barber, Service, Appointment
│   ├── forms.py              # AppointmentForm, AppointmentStatusForm
│   ├── views.py               # home, book, slots API, dashboard, status/cancel
│   ├── urls.py
│   ├── admin.py
│   ├── tests.py
│   ├── management/commands/seed_data.py
│   └── templates/booking/
├── templates/                # base.html, registration/login.html
└── static/css/style.css
```

## 6. Setup Instructions

```bash
# 1. Clone/extract the project and enter the folder
cd primecutz_project

# 2. Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Apply database migrations
python manage.py migrate

# 5. (Optional) Load demo barbers & services
python manage.py seed_data

# 6. Create a staff/admin account
python manage.py createsuperuser

# 7. Run the development server
python manage.py runserver
```

Then visit:
- `http://127.0.0.1:8000/` — public site / booking
- `http://127.0.0.1:8000/dashboard/` — staff dashboard (login required)
- `http://127.0.0.1:8000/admin/` — Django admin

Run the test suite with:
```bash
python manage.py test booking
```

## 7. Demo Login (after `createsuperuser`, or use your own)

Set your own credentials with `python manage.py createsuperuser`. This
project deliberately does not ship hardcoded credentials for security.

## 8. Possible Extensions (future work)

- Email/SMS reminders (an `EMAIL_BACKEND` is already configured — swap the
  console backend for SMTP and add a `post_save` signal to notify clients).
- Barber-specific login so each barber only sees their own bookings.
- Recurring appointments / customer accounts with booking history.
- Payment integration (e.g. Paystack, since this targets a Nigerian business).

---
*Built for SEN 310 — Web Application Development, using Python & Django.*
