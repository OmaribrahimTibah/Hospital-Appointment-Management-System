# Hospital Appointment Management System

A command-line hospital appointment management project converted from the supplied Java classes to Python.

## Features
- Admin, doctor, and patient login
- Add doctors and register patients
- Assign patients to doctors
- Create, view, and cancel appointments
- Prevent overlapping appointments for the same doctor
- Update appointment status
- Search records and generate basic reports
- Persistent JSON storage in the `data/` folder
- Password hashing for newly created accounts

## Requirements
- Python 3.9+
- No third-party packages required

## Run
```bash
python main.py
```

On first run, a default administrator is created:

- Username: `admin`
- Password: `admin123`

**Change/remove the default credentials before using this project with real data.**

## Project structure
```text
hospital_appointment_system/
├── main.py
├── hospital_system.py
├── models.py
├── storage.py
├── data/                 # Created automatically; local data is not committed
├── .gitignore
└── README.md
```

## Data and privacy
The application stores records locally as JSON files in `data/`. Do not commit real patient data, passwords, or personal information to GitHub. The original Java program used plain-text passwords; this Python version hashes passwords for newly created users and upgrades an old plain-text password after a successful login. This is an educational CLI project, not a production-ready medical system.

## Notes about the conversion
The provided Java files referenced an `Appointment` class, but no `Appointment.java` file was included. The Python `Appointment` model was reconstructed from the fields and methods used by the supplied classes: appointment ID, patient ID, doctor ID, date, time, and status.
