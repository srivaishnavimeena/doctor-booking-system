import tkinter as tk
from tkinter import ttk, messagebox
import db


def open_window(parent):
    win = tk.Toplevel(parent)
    win.title("Book Appointment")
    win.geometry("480x560")

    dept_map = {name: i for i, name in db.get_departments()}
    doc_map = {}
    patient_var = tk.StringVar()
    dept_var = tk.StringVar()
    doc_var = tk.StringVar()
    date_var = tk.StringVar()
    info_var = tk.StringVar()

    frm = ttk.LabelFrame(win, text="New Appointment", padding=12)
    frm.pack(fill="both", expand=True, padx=12, pady=12)

    def row(r, label, widget):
        ttk.Label(frm, text=label).grid(row=r, column=0, sticky="w", pady=6)
        widget.grid(row=r, column=1, pady=6, padx=8)

    patient_box = ttk.Combobox(frm, textvariable=patient_var, width=30, state="readonly")
    patient_box["values"] = [f"{p[0]} - {p[1]}" for p in db.get_patients()]
    row(0, "Patient", patient_box)

    dept_box = ttk.Combobox(frm, textvariable=dept_var, width=30, state="readonly",
                            values=list(dept_map.keys()))
    row(1, "Department", dept_box)

    doc_box = ttk.Combobox(frm, textvariable=doc_var, width=30, state="readonly")
    row(2, "Doctor", doc_box)

    date_box = ttk.Combobox(frm, textvariable=date_var, width=30, state="readonly",
                            values=db.upcoming_dates(14))
    row(3, "Date", date_box)

    ttk.Label(frm, textvariable=info_var, foreground="gray").grid(
        row=4, column=0, columnspan=2, sticky="w", pady=(10, 2))
    slots_list = tk.Listbox(frm, height=10, width=40, exportselection=False)
    slots_list.grid(row=5, column=0, columnspan=2, pady=4)

    def on_dept(event=None):
        doc_map.clear()
        for d in db.get_doctors_by_dept(dept_map[dept_var.get()]):
            doc_map[f"{d[0]} - {d[1]}"] = d[0]
        doc_box["values"] = list(doc_map.keys())
        doc_var.set("")
        show_slots()

    def show_slots(event=None):
        slots_list.delete(0, "end")
        if doc_var.get() not in doc_map or not date_var.get():
            info_var.set("Choose a doctor and a date to see free slots")
            return
        slots = db.get_free_slots(doc_map[doc_var.get()], date_var.get())
        for s in slots:
            slots_list.insert("end", s)
        info_var.set(f"{len(slots)} free slot(s)" if slots else
                     "No free slots (doctor not available that day, or fully booked)")

    def book():
        if not patient_var.get():
            messagebox.showwarning("Missing", "Choose a patient")
            return
        if doc_var.get() not in doc_map or not date_var.get():
            messagebox.showwarning("Missing", "Choose a doctor and a date")
            return
        sel = slots_list.curselection()
        if not sel:
            messagebox.showwarning("Missing", "Pick a time slot")
            return
        slot = slots_list.get(sel[0])
        patient_id = int(patient_var.get().split(" - ", 1)[0])
        ok = db.book_appointment(doc_map[doc_var.get()], patient_id, date_var.get(), slot)
        if ok:
            messagebox.showinfo("Booked", f"Appointment confirmed for {date_var.get()} at {slot}")
        else:
            messagebox.showerror("Taken", "That slot was just booked by someone else")
        show_slots()

    ttk.Button(frm, text="Book Appointment", command=book).grid(
        row=6, column=0, columnspan=2, pady=14)

    dept_box.bind("<<ComboboxSelected>>", on_dept)
    doc_box.bind("<<ComboboxSelected>>", show_slots)
    date_box.bind("<<ComboboxSelected>>", show_slots)
    show_slots()