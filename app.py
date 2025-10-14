from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
from datetime import datetime
import secrets
import string

# --- CONFIGURATION ---
app = Flask(__name__)
# Generate a secure secret key for session management (CRITICAL for security)
app.secret_key = secrets.token_hex(16) 
DB_FILE = "device_loans.db"
# ---------------------

# --- AUTHENTICATION SETUP ---
def generate_credentials():
    """Generates a secure, random username and password on application start."""
    # Username: prefix + 4 random digits
    username_chars = string.digits
    # Password: 16 characters from letters, digits, and punctuation
    password_chars = string.ascii_letters + string.digits + string.punctuation
    
    admin_username = "admin_" + ''.join(secrets.choice(username_chars) for i in range(4))
    admin_password = ''.join(secrets.choice(password_chars) for i in range(16))
    return admin_username, admin_password

# Generate credentials when the module is loaded
ADMIN_USERNAME, ADMIN_PASSWORD = generate_credentials()

# This is the section that pastes the login details to the terminal
print("\n--- NEW ADMIN CREDENTIALS (Valid for this session only) ---")
print(f"URL: /login")
print(f"Username: {ADMIN_USERNAME}")
print(f"Password: {ADMIN_PASSWORD}")
print("-----------------------------------------------------------\n")
# ----------------------------

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

# --- ROUTES ---

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session["logged_in"] = True
            flash("Login successful! Welcome to the Admin Panel.", "success")
            return redirect(url_for("admin"))
        else:
            flash("Invalid username or password. Please try again.", "error")
            return redirect(url_for("login"))

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("logged_in", None)
    flash("You have been successfully logged out.", "info")
    return redirect(url_for("index"))

@app.route("/loan", methods=["GET", "POST"])
def loan():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    if request.method == "POST":
        name = request.form["name"]
        surname = request.form["surname"]
        email = request.form["email"]
        # The selected device ID is now handled by the form post
        device_id = request.form["selected_device_id"]
        
        if not device_id:
             flash("Please select a device to loan.", "error")
             conn.close()
             return redirect(url_for("loan"))

        # 1. Insert student
        c.execute("INSERT INTO students (name, surname, email) VALUES (?, ?, ?)", (name, surname, email))
        student_id = c.lastrowid
        
        # 2. Insert loan and log time
        loan_time = datetime.now().isoformat()
        c.execute("INSERT INTO loans (student_id, device_id, loan_time) VALUES (?, ?, ?)", (student_id, device_id, loan_time))
        
        # 3. Update device availability to 0 (Loaned Out)
        c.execute("UPDATE devices SET available = 0 WHERE id = ?", (device_id,))
        conn.commit()
        flash("Device loaned successfully! Remember to return it on time.", "success")
        return redirect(url_for("loan"))
    else:
        # GET request: fetch all available devices with detailed information
        c.execute("SELECT id, rubric_id, suffix_id, category FROM devices WHERE available = 1 ORDER BY category, rubric_id")
        devices = c.fetchall()
        conn.close()
        # Pass a list of categories for the filter dropdown
        categories = sorted(list(set(d[3] for d in devices)))
        return render_template("loan.html", devices=devices, categories=categories)

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
        flash("Device returned successfully!", "success")
        return redirect(url_for("return_device"))
    else:
        # Fetch students who have active loans
        c.execute("""
            SELECT s.id, s.name || ' ' || s.surname 
            FROM students s 
            JOIN loans l ON s.id = l.student_id 
            WHERE l.return_time IS NULL 
            GROUP BY s.id
        """)
        students = c.fetchall()
        
        # Fetch devices that are currently loaned out
        c.execute("SELECT id, rubric_id || '-' || suffix_id || ' (' || category || ')' FROM devices WHERE available = 0")
        devices = c.fetchall()
        
        conn.close()
        return render_template("return.html", students=students, devices=devices)

@app.route("/admin", methods=["GET", "POST"])
def admin():
    # Enforce login requirement
    if not session.get("logged_in"):
        flash("Access denied. Please log in to view the Admin Panel.", "warning")
        return redirect(url_for("login"))
        
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    if request.method == "POST":
        if "delete_id" in request.form:
            # Handle Device Deletion
            device_id = request.form["delete_id"]
            c.execute("DELETE FROM devices WHERE id = ?", (device_id,))
            conn.commit()
            flash("Device deleted successfully!", "success")
            
        else:
            # Handle New Device Addition
            rubric_id = request.form["rubric_id"]
            suffix_id = request.form["suffix_id"]
            category = request.form["category"]
            
            c.execute("INSERT INTO devices (rubric_id, suffix_id, category, available) VALUES (?, ?, ?, 1)", (rubric_id, suffix_id, category))
            conn.commit()
            flash("Device added successfully!", "success")
            
        return redirect(url_for("admin"))
        
    else:
        # GET request: Display all data
        c.execute("SELECT * FROM students")
        students = c.fetchall()
        c.execute("SELECT id, rubric_id, suffix_id, category, available FROM devices")
        devices = c.fetchall()
        c.execute("SELECT * FROM loans")
        loans = c.fetchall()
        conn.close()
        return render_template("admin.html", students=students, devices=devices, loans=loans)

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
