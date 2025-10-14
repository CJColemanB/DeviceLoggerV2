from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
from datetime import datetime

# --- CONFIGURATION ---
app = Flask(__name__)
# IMPORTANT: In a real application, use an environment variable for a secret key.
app.secret_key = "supersecretkey" 
DB_FILE = "device_loans.db"
# ---------------------

# Initialize database
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # Devices Table
    c.execute('''CREATE TABLE IF NOT EXISTS devices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    rubric_id TEXT,
                    suffix_id TEXT,
                    category TEXT,
                    available INTEGER -- 1 for Loanable/Available, 0 for Loaned Out
                )''')
    # Students Table
    c.execute('''CREATE TABLE IF NOT EXISTS students (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    surname TEXT,
                    email TEXT
                )''')
    # Loans Table
    c.execute('''CREATE TABLE IF NOT EXISTS loans (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id INTEGER,
                    device_id INTEGER,
                    loan_time TEXT,
                    return_time TEXT,
                    FOREIGN KEY(student_id) REFERENCES students(id),
                    FOREIGN KEY(device_id) REFERENCES devices(id)
                )''')
    conn.commit()
    conn.close()

@app.route("/")
def index():
    # Assuming this route serves a simple home page or navigation menu
    return render_template("index.html")

@app.route("/loan", methods=["GET", "POST"])
def loan():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    if request.method == "POST":
        name = request.form["name"]
        surname = request.form["surname"]
        email = request.form["email"]
        device_id = request.form["device"]
        
        # Insert student (Note: in a real app, you'd check if student exists first)
        c.execute("INSERT INTO students (name, surname, email) VALUES (?, ?, ?)", (name, surname, email))
        student_id = c.lastrowid
        
        # Insert loan
        loan_time = datetime.now().isoformat()
        c.execute("INSERT INTO loans (student_id, device_id, loan_time) VALUES (?, ?, ?)", (student_id, device_id, loan_time))
        
        # Update device availability (0 = Loaned Out)
        c.execute("UPDATE devices SET available = 0 WHERE id = ?", (device_id,))
        conn.commit()
        flash("Device loaned successfully!")
        return redirect(url_for("loan"))
    else:
        # Get all available devices
        c.execute("SELECT id, rubric_id || '-' || suffix_id || ' (' || category || ')' FROM devices WHERE available = 1")
        devices = c.fetchall()
        conn.close()
        return render_template("loan.html", devices=devices)

@app.route("/return", methods=["GET", "POST"])
def return_device():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    if request.method == "POST":
        student_id = request.form["student"]
        device_id = request.form["device"]
        return_time = datetime.now().isoformat()
        
        # Update loan record
        c.execute("UPDATE loans SET return_time = ? WHERE student_id = ? AND device_id = ? AND return_time IS NULL", (return_time, student_id, device_id))
        
        # Update device availability (1 = Available)
        c.execute("UPDATE devices SET available = 1 WHERE id = ?", (device_id,))
        conn.commit()
        flash("Device returned successfully!")
        return redirect(url_for("return_device"))
    else:
        # Get all students
        c.execute("SELECT id, name || ' ' || surname FROM students")
        students = c.fetchall()
        # Get all currently loaned out devices
        c.execute("SELECT id, rubric_id || '-' || suffix_id || ' (' || category || ')' FROM devices WHERE available = 0")
        devices = c.fetchall()
        conn.close()
        return render_template("return.html", students=students, devices=devices)

@app.route("/admin", methods=["GET", "POST"])
def admin():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    if request.method == "POST":
        if "delete_id" in request.form:
            # Handle Device Deletion
            device_id = request.form["delete_id"]
            # To prevent foreign key errors, you should first check if the device 
            # is part of an active loan. For simplicity here, we just delete the device.
            c.execute("DELETE FROM devices WHERE id = ?", (device_id,))
            conn.commit()
            flash("Device deleted successfully!")
            
        else:
            # Handle New Device Addition
            rubric_id = request.form["rubric_id"]
            suffix_id = request.form["suffix_id"]
            category = request.form["category"]
            
            # Insert device with default 'available' status set to 1 (Loanable)
            c.execute("INSERT INTO devices (rubric_id, suffix_id, category, available) VALUES (?, ?, ?, 1)", (rubric_id, suffix_id, category))
            conn.commit()
            flash("Device added successfully!")
            
        return redirect(url_for("admin"))
        
    else:
        # GET request: Display all data
        c.execute("SELECT * FROM students")
        students = c.fetchall()
        # Select all device data: ID, Rubric, Suffix, Category, Available
        c.execute("SELECT id, rubric_id, suffix_id, category, available FROM devices")
        devices = c.fetchall()
        c.execute("SELECT * FROM loans")
        loans = c.fetchall()
        conn.close()
        return render_template("admin.html", students=students, devices=devices, loans=loans)

# The separate delete_device function is no longer needed as the logic is in the /admin POST handler.
# @app.route("/delete_device/<int:device_id>")
# def delete_device(device_id):
#     ...

if __name__ == "__main__":
    init_db()
    # Setting debug=False is recommended for production environments
    app.run(debug=True)
