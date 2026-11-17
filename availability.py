import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import db

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday",
        "Friday", "Saturday", "Sunday"]


def open_window(parent):
    win = tk.Toplevel(parent)
    win.title("Doctor Availability")
    win.geometry("720x420")

    doc_var = tk.StringVar()
    day_var = tk.StringVar()
    start_var = tk.StringVar(value="09:00")
    end_var = tk.StringVar(value="13:00")

    form = ttk.LabelFrame(win, text="Set Availability", padding=10)
    form.pack(side="left", fill="y", padx=10, pady=10)

    ttk.Label(form, text="Doctor").grid(row=0, column=0, sticky="w", pady=4)
    doc_box = ttk.Combobox(form, textvariable=doc_var, width=26, state="readonly")
    doc_box.grid(row=0, column=1, pady=4)

    ttk.Label(form, text="Day").grid(row=1, column=0, sticky="w", pady=4)
    ttk.Combobox(form, textvariable=day_var, values=DAYS, width=26,
                 state="readonly").grid(row=1, column=1, pady=4)

    ttk.Label(form, text="Start (HH:MM)").grid(row=2, column=0, sticky="w", pady=4)
    ttk.Entry(form, textvariable=start_var, width=28).grid(row=2, column=1, pady=4)

    ttk.Label(form, text="End (HH:MM)").grid(row=3, column=0, sticky="w", pady=4)
    ttk.Entry(form, textvariable=end_var, width=28).grid(row=3, column=1, pady=4)

    right = ttk.Frame(win)
    right.pack(side="right", fill="both", expand=True, padx=10, pady=10)
    ttk.Label(right, text="Working hours of the selected doctor").pack(anchor="w")

    cols = ("ID", "Day", "Start", "End")
    tree = ttk.Treeview(right, columns=cols, show="headings", height=14)
    for c, w in zip(cols, (50, 130, 100, 100)):
        tree.heading(c, text=c)
        tree.column(c, width=w)
    tree.pack(fill="both", expand=True, pady=8)

    def load_doctors():
        doc_box["values"] = [f"{d[0]} - {d[1]}" for d in db.get_doctors()]

    def doctor_id():
        v = doc_var.get()
        return int(v.split(" - ", 1)[0]) if v else None

    def load_table(event=None):
        tree.delete(*tree.get_children())
        did = doctor_id()
        if did is None:
            return
        for r in db.get_availability(did):
            tree.insert("", "end", iid=str(r[0]), values=r)

    def add():
        did = doctor_id()
        if did is None or not day_var.get():
            messagebox.showwarning("Missing", "Choose a doctor and a day")
            return
        try:
            s = datetime.strptime(start_var.get().strip(), "%H:%M")
            e = datetime.strptime(end_var.get().strip(), "%H:%M")
        except ValueError:
            messagebox.showwarning("Invalid", "Use 24-hour time like 09:00 or 14:30")
            return
        if s >= e:
            messagebox.showwarning("Invalid", "End time must be after start time")
            return
        db.add_availability(did, day_var.get(), s.strftime("%H:%M"), e.strftime("%H:%M"))
        load_table()

    def delete():
        iid = tree.focus()
        if not iid:
            messagebox.showwarning("Select", "Click a row in the table first")
            return
        if messagebox.askyesno("Confirm", "Delete this time range?"):
            db.delete_availability(int(iid))
            load_table()

    btns = ttk.Frame(form)
    btns.grid(row=4, column=0, columnspan=2, pady=12)
    ttk.Button(btns, text="Add", width=10, command=add).pack(side="left", padx=4)
    ttk.Button(btns, text="Delete Selected", width=15, command=delete).pack(side="left", padx=4)

    doc_box.bind("<<ComboboxSelected>>", load_table)
    load_doctors()