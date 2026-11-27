from dataclasses import dataclass, asdict, field
from typing import Optional

@dataclass
class User:
    id: str
    phone_number: str
    name: str
    username: str
    password_hash: str = field(repr=False)

@dataclass
class Admin(User):
    pass

@dataclass
class Doctor(User):
    specialization: str
    department: str

@dataclass
class Patient(User):
    age: int
    gender: str
    assigned_doctor_id: Optional[str] = None

@dataclass
class Appointment:
    id: str
    patient_id: str
    doctor_id: str
    date: str
    time: str
    status: str = "Confirmed"

    def set_status(self, status: str) -> None:
        allowed = {"Confirmed", "Completed", "Cancelled"}
        if status not in allowed:
            raise ValueError("Invalid appointment status.")
        if self.status == "Cancelled" and status == "Completed":
            raise ValueError("A cancelled appointment cannot be completed.")
        self.status = status

def user_to_dict(user):
    return asdict(user)

def appointment_to_dict(appointment):
    return asdict(appointment)
