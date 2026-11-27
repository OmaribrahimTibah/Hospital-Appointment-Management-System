from datetime import date as date_type, time as time_type
from getpass import getpass
from hashlib import pbkdf2_hmac
from secrets import token_hex
from models import Admin, Doctor, Patient, Appointment
from storage import Storage

ITERATIONS = 310_000

def hash_password(password, salt=None):
    salt = salt or token_hex(16)
    digest = pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt), ITERATIONS)
    return f"{salt}${digest.hex()}"

def verify_password(password, stored):
    try:
        salt, expected = stored.split("$", 1)
        actual = pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt), ITERATIONS).hex()
        return actual == expected
    except (ValueError, TypeError):
        return password == stored

class HospitalSystem:
    def __init__(self, data_dir="data"):
        self.storage = Storage(data_dir)
        self.admins = self.storage.load_admins()
        self.doctors = self.storage.load_doctors()
        self.patients = self.storage.load_patients()
        self.appointments = self.storage.load_appointments()
        if not self.admins:
            self.admins.append(Admin("A001", "0123456789", "System Admin", "admin",
                                     hash_password("admin123")))
            self.save()

    def save(self):
        self.storage.save_all(self.admins, self.doctors, self.patients, self.appointments)

    @staticmethod
    def ask(prompt, secret=False):
        value = getpass(prompt) if secret else input(prompt)
        return value.strip()

    @staticmethod
    def next_id(prefix, objects):
        used = {obj.id for obj in objects}
        number = 1
        while f"{prefix}{number:03d}" in used:
            number += 1
        return f"{prefix}{number:03d}"

    def find_by_username(self, users, username):
        return next((u for u in users if u.username.casefold() == username.casefold()), None)

    def login(self, role, users):
        print(f"\n--- {role} Login ---")
        username = self.ask("Username: ")
        password = self.ask("Password: ", secret=True)
        user = self.find_by_username(users, username)
        if user and verify_password(password, user.password_hash):
            if "$" not in user.password_hash:
                user.password_hash = hash_password(password)
                self.save()
            print(f"Login successful. Welcome, {user.name}.")
            return user
        print("Login failed. Invalid username or password.")
        return None

    def start(self):
        while True:
            print("\n===== HOSPITAL APPOINTMENT MANAGEMENT SYSTEM =====")
            print("1. Login as Admin\n2. Login as Doctor\n3. Login as Patient\n4. Exit")
            choice = self.ask("Select your role: ")
            if choice == "1":
                user = self.login("Admin", self.admins)
                if user: self.admin_menu(user)
            elif choice == "2":
                user = self.login("Doctor", self.doctors)
                if user: self.doctor_menu(user)
            elif choice == "3":
                user = self.login("Patient", self.patients)
                if user: self.patient_menu(user)
            elif choice == "4":
                self.save()
                print("Data saved. Goodbye!")
                break
            else:
                print("Invalid choice. Please enter 1-4.")

    def unique_username(self, username):
        all_users = self.admins + self.doctors + self.patients
        return not any(u.username.casefold() == username.casefold() for u in all_users)

    def admin_menu(self, admin):
        while True:
            print("\n===== ADMIN MENU =====")
            print("1. Add Doctor\n2. Register Patient\n3. Assign Patient to Doctor")
            print("4. Create Appointment\n5. View All Doctors\n6. View All Patients")
            print("7. View All Appointments\n8. Search Patient by ID\n9. Search Doctor by ID")
            print("10. Generate Reports\n11. Save Data\n12. Logout")
            choice = self.ask("Enter choice: ")
            actions = {
                "1": self.add_doctor, "2": self.register_patient,
                "3": self.assign_patient, "4": self.admin_create_appointment,
                "5": self.view_doctors, "6": self.view_patients,
                "7": self.view_appointments, "8": self.search_patient,
                "9": self.search_doctor, "10": self.reports,
            }
            if choice in actions:
                actions[choice]()
            elif choice == "11":
                self.save(); print("Data saved successfully.")
            elif choice == "12":
                self.save(); print("Logging out...")
                return
            else:
                print("Invalid choice.")

    def add_doctor(self):
        print("\n--- Add Doctor ---")
        name = self.ask("Name: ")
        username = self.ask("Username: ")
        if not name or not username or not self.unique_username(username):
            print("Name/username is empty or username already exists."); return
        password = self.ask("Password: ", secret=True)
        specialization = self.ask("Specialization: ")
        department = self.ask("Department: ")
        phone = self.ask("Phone number: ")
        self.doctors.append(Doctor(self.next_id("D", self.doctors), phone, name, username,
                                   hash_password(password), specialization, department))
        self.save()
        print("Doctor added.")

    def register_patient(self):
        print("\n--- Register Patient ---")
        name = self.ask("Name: ")
        username = self.ask("Username: ")
        if not name or not username or not self.unique_username(username):
            print("Name/username is empty or username already exists."); return
        password = self.ask("Password: ", secret=True)
        try:
            age = int(self.ask("Age: "))
            if age <= 0: raise ValueError
        except ValueError:
            print("Age must be a positive integer."); return
        gender = self.ask("Gender: ")
        phone = self.ask("Phone number: ")
        self.patients.append(Patient(self.next_id("P", self.patients), phone, name, username,
                                     hash_password(password), age, gender, None))
        self.save()
        print("Patient registered.")

    def assign_patient(self):
        patient = self.get_by_id(self.patients, self.ask("Patient ID: "))
        doctor = self.get_by_id(self.doctors, self.ask("Doctor ID: "))
        if not patient or not doctor:
            print("Patient or doctor not found."); return
        patient.assigned_doctor_id = doctor.id
        self.save()
        print(f"{patient.name} assigned to Dr. {doctor.name}.")

    def admin_create_appointment(self):
        patient = self.get_by_id(self.patients, self.ask("Patient ID: "))
        doctor = self.get_by_id(self.doctors, self.ask("Doctor ID: "))
        if not patient or not doctor:
            print("Invalid patient or doctor ID."); return
        self.create_appointment(patient, doctor)

    def create_appointment(self, patient, doctor):
        try:
            appointment_date = self.ask("Date (YYYY-MM-DD): ")
            appointment_time = self.ask("Time (HH:MM): ")
            date_type.fromisoformat(appointment_date)
            time_type.fromisoformat(appointment_time)
        except ValueError:
            print("Invalid date/time. Use YYYY-MM-DD and HH:MM."); return
        if any(a.doctor_id == doctor.id and a.date == appointment_date and
               a.time == appointment_time and a.status != "Cancelled"
               for a in self.appointments):
            print("This doctor already has an active appointment at that time."); return
        appointment = Appointment(self.next_id("A", self.appointments), patient.id,
                                  doctor.id, appointment_date, appointment_time)
        self.appointments.append(appointment)
        self.save()
        print(f"Appointment created: {appointment.id}")

    @staticmethod
    def get_by_id(objects, object_id):
        return next((obj for obj in objects if obj.id.casefold() == object_id.casefold()), None)

    def view_doctors(self):
        print("\n--- Doctors ---")
        if not self.doctors: print("No doctors found.")
        for d in self.doctors:
            print(f"{d.id} | {d.name} | {d.specialization} | {d.department}")

    def view_patients(self):
        print("\n--- Patients ---")
        if not self.patients: print("No patients found.")
        for p in self.patients:
            print(f"{p.id} | {p.name} | Assigned doctor: {p.assigned_doctor_id or 'None'}")

    def view_appointments(self, appointments=None):
        print("\n--- Appointments ---")
        rows = self.appointments if appointments is None else appointments
        if not rows: print("No appointments found.")
        for a in rows:
            print(f"{a.id} | Patient: {a.patient_id} | Doctor: {a.doctor_id} | "
                  f"{a.date} {a.time} | {a.status}")

    def search_patient(self):
        p = self.get_by_id(self.patients, self.ask("Patient ID: "))
        if p: print(p)
        else: print("Patient not found.")

    def search_doctor(self):
        d = self.get_by_id(self.doctors, self.ask("Doctor ID: "))
        if d: print(d)
        else: print("Doctor not found.")

    def reports(self):
        print("\n===== HOSPITAL REPORTS =====")
        print(f"Doctors: {len(self.doctors)} | Patients: {len(self.patients)}")
        for status in ("Confirmed", "Completed", "Cancelled"):
            print(f"{status}: {sum(a.status == status for a in self.appointments)}")
        counts = {d.id: sum(a.doctor_id == d.id for a in self.appointments)
                  for d in self.doctors}
        print("Top doctors by appointment count:")
        for doctor in sorted(self.doctors, key=lambda d: (-counts[d.id], d.name))[:3]:
            print(f"{doctor.name} ({doctor.id}): {counts[doctor.id]}")

    def doctor_menu(self, doctor):
        while True:
            print("\n===== DOCTOR MENU =====")
            print("1. View Profile\n2. View Assigned Patients\n3. View My Appointments")
            print("4. Update Appointment Status\n5. Logout")
            choice = self.ask("Enter choice: ")
            if choice == "1":
                print(doctor)
            elif choice == "2":
                assigned = [p for p in self.patients if p.assigned_doctor_id == doctor.id]
                for p in assigned: print(f"{p.id} - {p.name}, age {p.age}, phone {p.phone_number}")
                if not assigned: print("No patients assigned.")
            elif choice == "3":
                self.view_appointments([a for a in self.appointments if a.doctor_id == doctor.id])
            elif choice == "4":
                self.update_status([a for a in self.appointments if a.doctor_id == doctor.id])
            elif choice == "5":
                self.save(); return
            else: print("Invalid choice.")

    def update_status(self, appointments):
        if not appointments:
            print("No appointments to update."); return
        for i, a in enumerate(appointments, 1):
            print(f"{i}. {a.id} | {a.patient_id} | {a.date} {a.time} | {a.status}")
        try:
            selection = int(self.ask("Select appointment (0 to cancel): "))
            if selection == 0: return
            chosen = appointments[selection - 1]
            if selection < 1: raise IndexError
        except (ValueError, IndexError):
            print("Invalid selection."); return
        print("1. Confirmed\n2. Completed\n3. Cancelled")
        status_choice = self.ask("New status: ")
        status = {"1": "Confirmed", "2": "Completed", "3": "Cancelled"}.get(status_choice)
        if not status:
            print("Invalid status."); return
        try:
            chosen.set_status(status)
            self.save()
            print("Status updated.")
        except ValueError as exc:
            print(exc)

    def patient_menu(self, patient):
        while True:
            print("\n===== PATIENT MENU =====")
            print("1. View Profile\n2. View Assigned Doctor\n3. View My Appointments")
            print("4. Book Appointment\n5. Cancel Appointment\n6. Logout")
            choice = self.ask("Enter choice: ")
            if choice == "1":
                print(patient)
            elif choice == "2":
                doctor = self.get_by_id(self.doctors, patient.assigned_doctor_id or "")
                print(doctor if doctor else "You are not assigned to a doctor.")
            elif choice == "3":
                self.view_appointments([a for a in self.appointments if a.patient_id == patient.id])
            elif choice == "4":
                doctor = self.get_by_id(self.doctors, patient.assigned_doctor_id or "")
                if doctor: self.create_appointment(patient, doctor)
                else: print("You must be assigned to a doctor before booking.")
            elif choice == "5":
                self.cancel_patient_appointment(patient)
            elif choice == "6":
                self.save(); return
            else: print("Invalid choice.")

    def cancel_patient_appointment(self, patient):
        active = [a for a in self.appointments if a.patient_id == patient.id and a.status != "Cancelled"]
        if not active:
            print("No active appointments to cancel."); return
        for i, a in enumerate(active, 1):
            print(f"{i}. {a.id} | {a.date} {a.time} | {a.status}")
        try:
            selection = int(self.ask("Select appointment (0 to cancel): "))
            if selection == 0: return
            chosen = active[selection - 1]
            if selection < 1: raise IndexError
        except (ValueError, IndexError):
            print("Invalid selection."); return
        chosen.set_status("Cancelled")
        self.save()
        print("Appointment cancelled.")
