import tkinter as tk
from tkinter import ttk, messagebox
import importlib
import db

# button label -> module file that will open it
MODULES = {
    "Doctors": "doctors",
    "Availability": "availability",
    "Patients": "patients",
    "Book Appointment": "booking",
    "Appointments": "appointments",
}

ROLE_ACCESS = {
    "admin": list(MODULES.keys()),
    "receptionist": ["Patients", "Book Appointment", "Appointments"],
}


def open_dashboard(username, role):
    win = tk.Tk()
    win.title("Doctor Booking System - Dashboard")
    win.geometry("640x420")

    ttk.Label(win, text="Doctor Availability & Booking System",
              font=("Arial", 16, "bold")).pack(pady=(15, 2))
    ttk.Label(win, text=f"Logged in as {username} ({role})").pack()

    # ---- summary counts ----
    stats = ttk.Frame(win)
    stats.pack(pady=15)
    labels = {}
    for i, name in enumerate(["Doctors", "Patients", "Today's Appointments"]):
        box = ttk.LabelFrame(stats, text=name, padding=12)
        box.grid(row=0, column=i, padx=10)
        labels[name] = ttk.Label(box, text="0", font=("Arial", 20, "bold"))
        labels[name].pack()

    def refresh():
        labels["Doctors"].config(text=db.count("doctors"))
        labels["Patients"].config(text=db.count("patients"))
        labels["Today's Appointments"].config(text=db.count_today_appointments())

    # ---- navigation buttons ----
    def open_module(module_name):
        try:
            module = importlib.import_module(module_name)
        except ModuleNotFoundError:
            messagebox.showinfo("Coming soon", "This screen is not built yet.")
            return
        module.open_window(win)

    nav = ttk.Frame(win)
    nav.pack(pady=10)
    for i, label in enumerate(ROLE_ACCESS.get(role, [])):
        ttk.Button(nav, text=label, width=20,
                   command=lambda m=MODULES[label]: open_module(m)
                   ).grid(row=i // 2, column=i % 2, padx=8, pady=6)

    ttk.Button(win, text="Logout", command=win.destroy).pack(side="bottom", pady=12)

    refresh()
    win.bind("<FocusIn>", lambda e: refresh())   # counts update when you come back
    win.mainloop()