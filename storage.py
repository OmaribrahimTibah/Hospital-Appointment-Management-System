import json
from pathlib import Path
from dataclasses import asdict
from models import Admin, Doctor, Patient, Appointment

class Storage:
    def __init__(self, data_dir="data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.paths = {
            "admins": self.data_dir / "admins.json",
            "doctors": self.data_dir / "doctors.json",
            "patients": self.data_dir / "patients.json",
            "appointments": self.data_dir / "appointments.json",
        }

    def _read(self, key):
        path = self.paths[key]
        if not path.exists():
            return []
        try:
            with path.open("r", encoding="utf-8") as file:
                data = json.load(file)
            if not isinstance(data, list):
                raise ValueError("Expected a JSON list")
            return data
        except (json.JSONDecodeError, OSError, ValueError) as exc:
            raise RuntimeError(f"Could not read {path}: {exc}") from exc

    def _write(self, key, objects):
        path = self.paths[key]
        temp = path.with_suffix(path.suffix + ".tmp")
        with temp.open("w", encoding="utf-8") as file:
            json.dump([asdict(obj) for obj in objects], file, ensure_ascii=False, indent=4)
        temp.replace(path)

    def load_admins(self):
        return [Admin(**row) for row in self._read("admins")]

    def load_doctors(self):
        return [Doctor(**row) for row in self._read("doctors")]

    def load_patients(self):
        return [Patient(**row) for row in self._read("patients")]

    def load_appointments(self):
        return [Appointment(**row) for row in self._read("appointments")]

    def save_all(self, admins, doctors, patients, appointments):
        self._write("admins", admins)
        self._write("doctors", doctors)
        self._write("patients", patients)
        self._write("appointments", appointments)
