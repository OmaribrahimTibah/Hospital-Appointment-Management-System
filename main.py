from hospital_system import HospitalSystem

if __name__ == "__main__":
    try:
        HospitalSystem().start()
    except (KeyboardInterrupt, EOFError):
        print("\nExiting. Run again to continue.")
