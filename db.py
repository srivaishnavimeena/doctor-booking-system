import sqlite3
from datetime import datetime, timedelta, date

DB_NAME = "hospital.db"


def connect():
    return sqlite3.connect(DB_NAME, timeout=10)


CREATE_APPOINTMENTS = """
CREATE TABLE appointments(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    doctor_id INTEGER REFERENCES doctors(id),
    patient_id INTEGER REFERENCES patients(id),
    date TEXT NOT NULL,
    time TEXT NOT NULL,
    status TEXT DEFAULT 'Booked')
"""


def migrate_appointments(cur):
    """Rebuild the old table (inline UNIQUE rule) without losing data."""
    cur.execute("SELECT sql FROM sqlite_master "
                "WHERE type='table' AND name='appointments'")
    row = cur.fetchone()
    if not row:
        cur.execute(CREATE_APPOINTMENTS)
        return
    schema = row[0].replace(" ", "").replace("\n", "")
    if "UNIQUE(doctor_id,date,time)" in schema:
        cur.execute("ALTER TABLE appointments RENAME TO appointments_old")
        cur.execute(CREATE_APPOINTMENTS)
        cur.execute("""INSERT INTO appointments(id,doctor_id,patient_id,date,time,status)
                       SELECT id,doctor_id,patient_id,date,time,status
                       FROM appointments_old""")
        cur.execute("DROP TABLE appointments_old")


def init_db():
    con = connect()
    try:
        cur = con.cursor()
        cur.executescript("""
        CREATE TABLE IF NOT EXISTS departments(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL);

        CREATE TABLE IF NOT EXISTS doctors(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            dept_id INTEGER REFERENCES departments(id),
            phone TEXT);

        CREATE TABLE IF NOT EXISTS availability(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            doctor_id INTEGER REFERENCES doctors(id),
            day TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL);

        CREATE TABLE IF NOT EXISTS patients(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            age INTEGER,
            phone TEXT);

        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL);
        """)

        migrate_appointments(cur)

        cur.execute("""CREATE UNIQUE INDEX IF NOT EXISTS idx_active_slot
                       ON appointments(doctor_id, date, time)
                       WHERE status = 'Booked'""")

        cur.execute("INSERT OR IGNORE INTO users(username,password,role) "
                    "VALUES('admin','admin123','admin')")
        con.commit()
    finally:
        con.close()


# ---------- generic helper ----------
def run(query, params=(), fetch=False):
    con = connect()
    try:
        cur = con.cursor()
        cur.execute(query, params)
        rows = cur.fetchall() if fetch else None
        con.commit()
        return rows
    finally:
        con.close()


# ---------- users ----------
def add_user(username, password, role):
    run("INSERT OR IGNORE INTO users(username,password,role) VALUES(?,?,?)",
        (username, password, role))


def check_login(username, password):
    rows = run("SELECT role FROM users WHERE username=? AND password=?",
               (username, password), fetch=True)
    return rows[0][0] if rows else None


# ---------- departments ----------
def add_department(name):
    run("INSERT OR IGNORE INTO departments(name) VALUES(?)", (name,))


def get_departments():
    return run("SELECT id, name FROM departments", fetch=True)


# ---------- doctors ----------
def add_doctor(name, dept_id, phone):
    run("INSERT INTO doctors(name,dept_id,phone) VALUES(?,?,?)",
        (name, dept_id, phone))


def get_doctors(search=""):
    return run("""SELECT d.id, d.name, dep.name, d.phone
                  FROM doctors d
                  LEFT JOIN departments dep ON d.dept_id = dep.id
                  WHERE d.name LIKE ?""", (f"%{search}%",), fetch=True)


def get_doctors_by_dept(dept_id):
    return run("SELECT id, name FROM doctors WHERE dept_id=?", (dept_id,), fetch=True)


def update_doctor(doc_id, name, dept_id, phone):
    run("UPDATE doctors SET name=?, dept_id=?, phone=? WHERE id=?",
        (name, dept_id, phone, doc_id))


def delete_doctor(doc_id):
    run("DELETE FROM doctors WHERE id=?", (doc_id,))


# ---------- availability ----------
def add_availability(doctor_id, day, start, end):
    run("INSERT INTO availability(doctor_id,day,start_time,end_time) VALUES(?,?,?,?)",
        (doctor_id, day, start, end))


def get_availability(doctor_id):
    return run("SELECT id, day, start_time, end_time FROM availability WHERE doctor_id=?",
               (doctor_id,), fetch=True)


def delete_availability(av_id):
    run("DELETE FROM availability WHERE id=?", (av_id,))


# ---------- patients ----------
def add_patient(name, age, phone):
    run("INSERT INTO patients(name,age,phone) VALUES(?,?,?)", (name, age, phone))


def get_patients(search=""):
    return run("SELECT id, name, age, phone FROM patients WHERE name LIKE ?",
               (f"%{search}%",), fetch=True)


def update_patient(pid, name, age, phone):
    run("UPDATE patients SET name=?, age=?, phone=? WHERE id=?",
        (name, age, phone, pid))


def delete_patient(pid):
    run("DELETE FROM patients WHERE id=?", (pid,))


# ---------- appointments ----------
def book_appointment(doctor_id, patient_id, date_str, time_str):
    try:
        run("INSERT INTO appointments(doctor_id,patient_id,date,time) VALUES(?,?,?,?)",
            (doctor_id, patient_id, date_str, time_str))
        return True
    except sqlite3.IntegrityError:   # slot already taken
        return False


def get_booked_times(doctor_id, date_str):
    rows = run("""SELECT time FROM appointments
                  WHERE doctor_id=? AND date=? AND status='Booked'""",
               (doctor_id, date_str), fetch=True)
    return [r[0] for r in rows]


def cancel_appointment(app_id):
    run("UPDATE appointments SET status='Cancelled' WHERE id=?", (app_id,))


def get_appointments(search=""):
    return run("""SELECT a.id, a.doctor_id, d.name, p.name, a.date, a.time, a.status
                  FROM appointments a
                  JOIN doctors d ON a.doctor_id = d.id
                  JOIN patients p ON a.patient_id = p.id
                  WHERE p.name LIKE ? OR d.name LIKE ?
                  ORDER BY a.date DESC, a.time""",
               (f"%{search}%", f"%{search}%"), fetch=True)


def reschedule_appointment(app_id, new_date, new_time):
    try:
        run("UPDATE appointments SET date=?, time=? WHERE id=?",
            (new_date, new_time, app_id))
        return True
    except sqlite3.IntegrityError:   # new slot already booked
        return False


# ---------- slot logic ----------
def upcoming_dates(n=14):
    today = datetime.now().date()
    return [(today + timedelta(days=i)).isoformat() for i in range(n)]


def get_free_slots(doctor_id, date_str, minutes=30):
    """Split the doctor's hours for that weekday into slots,
    then remove booked and past ones."""
    day = datetime.strptime(date_str, "%Y-%m-%d").strftime("%A")
    booked = set(get_booked_times(doctor_id, date_str))
    now = datetime.now()
    slots = set()
    for _id, d, start, end in get_availability(doctor_id):
        if d != day:
            continue
        t = datetime.strptime(f"{date_str} {start}", "%Y-%m-%d %H:%M")
        stop = datetime.strptime(f"{date_str} {end}", "%Y-%m-%d %H:%M")
        while t + timedelta(minutes=minutes) <= stop:
            label = t.strftime("%H:%M")
            if label not in booked and t > now:
                slots.add(label)
            t += timedelta(minutes=minutes)
    return sorted(slots)


# ---------- dashboard counts ----------
def count(table):
    # table name is fixed inside our code, never typed by a user
    return run(f"SELECT COUNT(*) FROM {table}", fetch=True)[0][0]


def count_today_appointments():
    return run("SELECT COUNT(*) FROM appointments WHERE date=? AND status='Booked'",
               (date.today().isoformat(),), fetch=True)[0][0]


if __name__ == "__main__":
    init_db()
    print("Database ready")