from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "supersecretkey"

DB_FILE = "device_loans.db"

# Initialize database
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS devices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    rubric_id TEXT,
                    suffix_id TEXT,
                    category TEXT,
                    available INTEGER
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS students (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    surname TEXT,
                    email TEXT
                )''')
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
        # Insert student
        c.execute("INSERT INTO students (name, surname, email) VALUES (?, ?, ?)", (name, surname, email))
        student_id = c.lastrowid
        # Insert loan
        loan_time = datetime.now().isoformat()
        c.execute("INSERT INTO loans (student_id, device_id, loan_time) VALUES (?, ?, ?)", (student_id, device_id, loan_time))
        # Update device availability
        c.execute("UPDATE devices SET available = 0 WHERE id = ?", (device_id,))
        conn.commit()
        flash("Device loaned successfully!")
        return redirect(url_for("loan"))
    else:
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
        c.execute("UPDATE loans SET return_time = ? WHERE student_id = ? AND device_id = ? AND return_time IS NULL", (return_time, student_id, device_id))
        c.execute("UPDATE devices SET available = 1 WHERE id = ?", (device_id,))
        conn.commit()
        flash("Device returned successfully!")
        return redirect(url_for("return_device"))
    else:
        c.execute("SELECT id, name || ' ' || surname FROM students")
        students = c.fetchall()
        c.execute("SELECT id, rubric_id || '-' || suffix_id || ' (' || category || ')' FROM devices WHERE available = 0")
        devices = c.fetchall()
        conn.close()
        return render_template("return.html", students=students, devices=devices)

@app.route("/admin", methods=["GET", "POST"])
def admin():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    if request.method == "POST":
        rubric_id = request.form["rubric_id"]
        suffix_id = request.form["suffix_id"]
        category = request.form["category"]
        c.execute("INSERT INTO devices (rubric_id, suffix_id, category, available) VALUES (?, ?, ?, 1)", (rubric_id, suffix_id, category))
        conn.commit()
        flash("Device added successfully!")
        return redirect(url_for("admin"))
    else:
        c.execute("SELECT * FROM students")
        students = c.fetchall()
        c.execute("SELECT * FROM devices")
        devices = c.fetchall()
        c.execute("SELECT * FROM loans")
        loans = c.fetchall()
        conn.close()
        return render_template("admin.html", students=students, devices=devices, loans=loans)

@app.route("/delete_device/<int:device_id>")
def delete_device(device_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM devices WHERE id = ?", (device_id,))
    conn.commit()
    conn.close()
    flash("Device deleted successfully!")
    return redirect(url_for("admin"))

if __name__ == "__main__":
    init_db()
    app.run(debug=True)