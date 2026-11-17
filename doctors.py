import tkinter as tk
from tkinter import ttk, messagebox
import db


def open_window(parent):
    win = tk.Toplevel(parent)
    win.title("Doctor Management")
    win.geometry("900x480")

    dept_map = {}      # department name -> id
    rows_cache = {}    # doctor id -> row, so phone numbers keep leading zeros
    selected = {"id": None}

    name_var = tk.StringVar()
    dept_var = tk.StringVar()
    phone_var = tk.StringVar()
    search_var = tk.StringVar()
    new_dept_var = tk.StringVar()

    # ---------- left: form ----------
    form = ttk.LabelFrame(win, text="Doctor Details", padding=10)
    form.pack(side="left", fill="y", padx=10, pady=10)

    ttk.Label(form, text="Name").grid(row=0, column=0, sticky="w", pady=4)
    ttk.Entry(form, textvariable=name_var, width=26).grid(row=0, column=1, pady=4)

    ttk.Label(form, text="Department").grid(row=1, column=0, sticky="w", pady=4)
    dept_box = ttk.Combobox(form, textvariable=dept_var, width=23, state="readonly")
    dept_box.grid(row=1, column=1, pady=4)

    ttk.Label(form, text="Phone").grid(row=2, column=0, sticky="w", pady=4)
    ttk.Entry(form, textvariable=phone_var, width=26).grid(row=2, column=1, pady=4)

    # ---------- right: search + table ----------
    right = ttk.Frame(win)
    right.pack(side="right", fill="both", expand=True, padx=10, pady=10)

    top = ttk.Frame(right)
    top.pack(fill="x")
    ttk.Label(top, text="Search").pack(side="left")
    ttk.Entry(top, textvariable=search_var, width=25).pack(side="left", padx=6)

    cols = ("ID", "Name", "Department", "Phone")
    tree = ttk.Treeview(right, columns=cols, show="headings", height=15)
    for c, w in zip(cols, (50, 180, 140, 120)):
        tree.heading(c, text=c)
        tree.column(c, width=w)
    tree.pack(fill="both", expand=True, pady=8)

    # ---------- functions ----------
    def load_departments():
        dept_map.clear()
        for dep_id, dep_name in db.get_departments():
            dept_map[dep_name] = dep_id
        dept_box["values"] = list(dept_map.keys())

    def load_table():
        tree.delete(*tree.get_children())
        rows_cache.clear()
        for r in db.get_doctors(search_var.get().strip()):
            rows_cache[r[0]] = r
            tree.insert("", "end", iid=str(r[0]),
                        values=(r[0], r[1], r[2] or "", r[3] or ""))

    def clear_form():
        selected["id"] = None
        name_var.set("")
        dept_var.set("")
        phone_var.set("")
        tree.selection_remove(tree.selection())

    def validate():
        name = name_var.get().strip()
        phone = phone_var.get().strip()
        if not name:
            messagebox.showwarning("Missing", "Enter the doctor's name")
            return None
        if dept_var.get() not in dept_map:
            messagebox.showwarning("Missing", "Choose a department")
            return None
        if phone and not (phone.isdigit() and len(phone) == 10):
            messagebox.showwarning("Invalid", "Phone must be 10 digits")
            return None
        return name, dept_map[dept_var.get()], phone

    def add():
        data = validate()
        if data:
            db.add_doctor(*data)
            load_table()
            clear_form()

    def update():
        if selected["id"] is None:
            messagebox.showwarning("Select", "Click a doctor in the table first")
            return
        data = validate()
        if data:
            db.update_doctor(selected["id"], *data)
            load_table()
            clear_form()

    def delete():
        if selected["id"] is None:
            messagebox.showwarning("Select", "Click a doctor in the table first")
            return
        if messagebox.askyesno("Confirm", "Delete this doctor?"):
            db.delete_doctor(selected["id"])
            load_table()
            clear_form()

    def on_select(event):
        iid = tree.focus()
        if not iid:
            return
        row = rows_cache[int(iid)]
        selected["id"] = row[0]
        name_var.set(row[1])
        dept_var.set(row[2] or "")
        phone_var.set(row[3] or "")

    def add_department():
        name = new_dept_var.get().strip()
        if name:
            db.add_department(name)
            new_dept_var.set("")
            load_departments()

    # ---------- buttons ----------
    btns = ttk.Frame(form)
    btns.grid(row=3, column=0, columnspan=2, pady=12)
    for text, cmd in (("Add", add), ("Update", update),
                      ("Delete", delete), ("Clear", clear_form)):
        ttk.Button(btns, text=text, width=8, command=cmd).pack(side="left", padx=3)

    dept_frame = ttk.LabelFrame(form, text="New Department", padding=8)
    dept_frame.grid(row=4, column=0, columnspan=2, pady=10, sticky="ew")
    ttk.Entry(dept_frame, textvariable=new_dept_var, width=18).pack(side="left")
    ttk.Button(dept_frame, text="Add", width=6, command=add_department).pack(side="left", padx=5)

    tree.bind("<<TreeviewSelect>>", on_select)
    search_var.trace_add("write", lambda *a: load_table())   # live search

    load_departments()
    load_table()