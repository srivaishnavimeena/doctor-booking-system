import tkinter as tk
from tkinter import ttk, messagebox
import db


def open_window(parent):
    win = tk.Toplevel(parent)
    win.title("Appointments")
    win.geometry("860x480")

    rows_cache = {}
    search_var = tk.StringVar()

    top = ttk.Frame(win)
    top.pack(fill="x", padx=10, pady=8)
    ttk.Label(top, text="Search (patient or doctor)").pack(side="left")
    ttk.Entry(top, textvariable=search_var, width=28).pack(side="left", padx=6)

    cols = ("ID", "Doctor", "Patient", "Date", "Time", "Status")
    tree = ttk.Treeview(win, columns=cols, show="headings", height=16)
    for c, w in zip(cols, (50, 190, 170, 100, 80, 90)):
        tree.heading(c, text=c)
        tree.column(c, width=w)
    tree.pack(fill="both", expand=True, padx=10)

    def load_table():
        tree.delete(*tree.get_children())
        rows_cache.clear()
        for r in db.get_appointments(search_var.get().strip()):
            rows_cache[r[0]] = r          # r = id, doctor_id, doctor, patient, date, time, status
            tree.insert("", "end", iid=str(r[0]),
                        values=(r[0], r[2], r[3], r[4], r[5], r[6]))

    def selected_booked():
        iid = tree.focus()
        if not iid:
            messagebox.showwarning("Select", "Click an appointment first")
            return None
        row = rows_cache[int(iid)]
        if row[6] != "Booked":
            messagebox.showinfo("Not active", "This appointment is already cancelled")
            return None
        return row

    def cancel():
        row = selected_booked()
        if row and messagebox.askyesno("Confirm", "Cancel this appointment?"):
            db.cancel_appointment(row[0])
            load_table()

    def reschedule():
        row = selected_booked()
        if not row:
            return
        pop = tk.Toplevel(win)
        pop.title("Reschedule")
        pop.geometry("320x170")
        pop.grab_set()

        date_var = tk.StringVar()
        slot_var = tk.StringVar()
        ttk.Label(pop, text="New date").grid(row=0, column=0, padx=10, pady=10, sticky="w")
        date_box = ttk.Combobox(pop, textvariable=date_var, state="readonly",
                                values=db.upcoming_dates(14), width=20)
        date_box.grid(row=0, column=1)
        ttk.Label(pop, text="New time").grid(row=1, column=0, padx=10, pady=10, sticky="w")
        slot_box = ttk.Combobox(pop, textvariable=slot_var, state="readonly", width=20)
        slot_box.grid(row=1, column=1)

        def fill_slots(event=None):
            slot_box["values"] = db.get_free_slots(row[1], date_var.get())
            slot_var.set("")

        def confirm():
            if not date_var.get() or not slot_var.get():
                messagebox.showwarning("Missing", "Choose a date and a time", parent=pop)
                return
            if db.reschedule_appointment(row[0], date_var.get(), slot_var.get()):
                messagebox.showinfo("Done", "Appointment rescheduled", parent=pop)
                pop.destroy()
                load_table()
            else:
                messagebox.showerror("Taken", "That slot is already booked", parent=pop)

        date_box.bind("<<ComboboxSelected>>", fill_slots)
        ttk.Button(pop, text="Confirm", command=confirm).grid(row=2, column=0, columnspan=2, pady=12)

    btns = ttk.Frame(win)
    btns.pack(pady=10)
    ttk.Button(btns, text="Cancel Appointment", command=cancel).pack(side="left", padx=6)
    ttk.Button(btns, text="Reschedule", command=reschedule).pack(side="left", padx=6)
    ttk.Button(btns, text="Refresh", command=load_table).pack(side="left", padx=6)

    search_var.trace_add("write", lambda *a: load_table())
    load_table()