import tkinter as tk
from tkinter import ttk, messagebox
import db


def open_window(parent):
    win = tk.Toplevel(parent)
    win.title("Patient Registration")
    win.geometry("850x450")

    rows_cache = {}
    selected = {"id": None}
    name_var = tk.StringVar()
    age_var = tk.StringVar()
    phone_var = tk.StringVar()
    search_var = tk.StringVar()

    form = ttk.LabelFrame(win, text="Patient Details", padding=10)
    form.pack(side="left", fill="y", padx=10, pady=10)
    for i, (label, var) in enumerate((("Name", name_var), ("Age", age_var), ("Phone", phone_var))):
        ttk.Label(form, text=label).grid(row=i, column=0, sticky="w", pady=4)
        ttk.Entry(form, textvariable=var, width=26).grid(row=i, column=1, pady=4)

    right = ttk.Frame(win)
    right.pack(side="right", fill="both", expand=True, padx=10, pady=10)
    top = ttk.Frame(right)
    top.pack(fill="x")
    ttk.Label(top, text="Search").pack(side="left")
    ttk.Entry(top, textvariable=search_var, width=25).pack(side="left", padx=6)

    cols = ("ID", "Name", "Age", "Phone")
    tree = ttk.Treeview(right, columns=cols, show="headings", height=14)
    for c, w in zip(cols, (50, 200, 60, 130)):
        tree.heading(c, text=c)
        tree.column(c, width=w)
    tree.pack(fill="both", expand=True, pady=8)

    def load_table():
        tree.delete(*tree.get_children())
        rows_cache.clear()
        for r in db.get_patients(search_var.get().strip()):
            rows_cache[r[0]] = r
            tree.insert("", "end", iid=str(r[0]),
                        values=(r[0], r[1], r[2] if r[2] is not None else "", r[3] or ""))

    def clear_form():
        selected["id"] = None
        name_var.set("")
        age_var.set("")
        phone_var.set("")
        tree.selection_remove(tree.selection())

    def validate():
        name = name_var.get().strip()
        age = age_var.get().strip()
        phone = phone_var.get().strip()
        if not name:
            messagebox.showwarning("Missing", "Enter the patient's name")
            return None
        if age and not (age.isdigit() and 0 <= int(age) <= 120):
            messagebox.showwarning("Invalid", "Age must be a number between 0 and 120")
            return None
        if phone and not (phone.isdigit() and len(phone) == 10):
            messagebox.showwarning("Invalid", "Phone must be 10 digits")
            return None
        return name, int(age) if age else None, phone

    def add():
        data = validate()
        if data:
            db.add_patient(*data)
            load_table()
            clear_form()

    def update():
        if selected["id"] is None:
            messagebox.showwarning("Select", "Click a patient in the table first")
            return
        data = validate()
        if data:
            db.update_patient(selected["id"], *data)
            load_table()
            clear_form()

    def delete():
        if selected["id"] is None:
            messagebox.showwarning("Select", "Click a patient in the table first")
            return
        if messagebox.askyesno("Confirm", "Delete this patient?"):
            db.delete_patient(selected["id"])
            load_table()
            clear_form()

    def on_select(event):
        iid = tree.focus()
        if not iid:
            return
        row = rows_cache[int(iid)]
        selected["id"] = row[0]
        name_var.set(row[1])
        age_var.set(row[2] if row[2] is not None else "")
        phone_var.set(row[3] or "")

    btns = ttk.Frame(form)
    btns.grid(row=3, column=0, columnspan=2, pady=12)
    for text, cmd in (("Add", add), ("Update", update), ("Delete", delete), ("Clear", clear_form)):
        ttk.Button(btns, text=text, width=8, command=cmd).pack(side="left", padx=3)

    tree.bind("<<TreeviewSelect>>", on_select)
    search_var.trace_add("write", lambda *a: load_table())
    load_table()