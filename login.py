import tkinter as tk
from tkinter import ttk, messagebox
import db
import dashboard

def start_login():
    root = tk.Tk()
    root.title("Doctor Booking System - Login")
    root.geometry("340x260")
    root.resizable(False, False)

    ttk.Label(root, text="Hospital Login", font=("Arial", 16, "bold")).pack(pady=15)

    ttk.Label(root, text="Username").pack()
    user_entry = ttk.Entry(root, width=28)
    user_entry.pack(pady=3)

    ttk.Label(root, text="Password").pack()
    pass_entry = ttk.Entry(root, width=28, show="*")
    pass_entry.pack(pady=3)

    def do_login():
        username = user_entry.get().strip()
        password = pass_entry.get().strip()
        if not username or not password:
            messagebox.showwarning("Missing", "Enter username and password")
            return
        role = db.check_login(username, password)
        if role:
            root.destroy()
            dashboard.open_dashboard(username, role)
        else:
            messagebox.showerror("Failed", "Invalid username or password")

    ttk.Button(root, text="Login", command=do_login).pack(pady=15)
    root.bind("<Return>", lambda e: do_login())
    root.mainloop()