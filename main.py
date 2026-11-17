import db
import login

db.init_db()
db.add_user("reception", "recep123", "receptionist")
for d in ["General Medicine", "Cardiology", "Pediatrics", "Orthopedics", "Dermatology"]:
    db.add_department(d)
login.start_login()