import secrets
import string
from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
from datetime import datetime
import sys

app = Flask(__name__)
# Generate a strong, unique secret key for session management
app.secret_key = secrets.token_hex(24)

DB_FILE = "device_loans.db"

# --- Admin Authentication Setup ---
# Credentials generated on startup for this instance
ADMIN_USERNAME = ""
ADMIN_PASSWORD = ""

def generate_credentials():
    """Generates unique username and password for this app instance."""
    global ADMIN_USERNAME, ADMIN_PASSWORD
    
    # Generate a unique username (e.g., admin_4589)
    random_suffix = ''.join(secrets.choice(string.digits) for _ in range(4))
    ADMIN_USERNAME = f"admin_{random_suffix}"
    
    # Generate a strong, complex password
    chars = string.ascii_letters + string.digits + "!@#$%^&*"
    ADMIN_PASSWORD = ''.join(secrets.choice(chars) for _ in range(16))

    # Print credentials to the terminal
    print("\n" + "="*50)
    print("!!! ADMIN ACCESS CREDENTIALS !!!")
    print(f"USERNAME: {ADMIN_USERNAME}")
    print(f"PASSWORD: {ADMIN_PASSWORD}")
    print("Please use these to log into the /admin panel.")
    print("Credentials are valid ONLY for this session.")
    print("="*50 + "\n")

# Initialize database
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # Ensure the devices table has the necessary columns
    c.execute('''CREATE TABLE IF NOT EXISTS devices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    rubric_id TEXT,
                    suffix_id TEXT,
                    category TEXT,
                    available INTEGER -- 1 for loanable, 0 for on loan
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS students (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    surname TEXT,
                    email TEXT UNIQUE
                )''')
    # Ensure the loans table has loan_time and return_time
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

# --- Utility Functions ---

def login_required(f):
    """Decorator to check if user is logged in."""
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session or not session['logged_in']:
            flash("You must log in to access the admin panel.", "error")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

def get_db_connection():
    """Opens a new database connection."""
    return sqlite3.connect(DB_FILE)

# --- Routes ---

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        
        # Check against the temporary credentials
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['logged_in'] = True
            flash("Logged in successfully!", "success")
            return redirect(url_for("admin"))
        else:
            flash("Invalid credentials. Please try again.", "error")
            return render_template("login.html")
    
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop('logged_in', None)
    flash("You have been logged out.", "success")
    return redirect(url_for("index"))


@app.route("/loan", methods=["GET", "POST"])
def loan():
    conn = get_db_connection()
    c = conn.cursor()
    
    if request.method == "POST":
        name = request.form.get("name")
        surname = request.form.get("surname")
        email = request.form.get("email")
        device_id = request.form.get("selected_device_id") # Changed to use the hidden field ID
        
        if not device_id:
            flash("Please select a device before attempting to loan.", "error")
            conn.close()
            return redirect(url_for("loan"))

        try:
            # Check if student already exists, or insert new one
            c.execute("SELECT id FROM students WHERE email = ?", (email,))
            student_row = c.fetchone()
            
            if student_row:
                student_id = student_row[0]
                # Update name/surname just in case
                c.execute("UPDATE students SET name = ?, surname = ? WHERE id = ?", (name, surname, student_id))
            else:
                # Insert new student
                c.execute("INSERT INTO students (name, surname, email) VALUES (?, ?, ?)", (name, surname, email))
                student_id = c.lastrowid
            
            # Check device availability just in case (though UI should prevent this)
            c.execute("SELECT available FROM devices WHERE id = ?", (device_id,))
            if c.fetchone()[0] == 0:
                flash("Error: Device is already on loan.", "error")
                conn.rollback()
                conn.close()
                return redirect(url_for("loan"))

            # Insert loan
            loan_time = datetime.now().isoformat()
            c.execute("INSERT INTO loans (student_id, device_id, loan_time) VALUES (?, ?, ?)", (student_id, device_id, loan_time))
            
            # Update device availability to 0 (On Loan)
            c.execute("UPDATE devices SET available = 0 WHERE id = ?", (device_id,))
            
            conn.commit()
            flash(f"Device ID {device_id} loaned successfully to {name}!", "success")
        
        except sqlite3.Error as e:
            flash(f"Database Error: {e}", "error")
            conn.rollback()

        conn.close()
        return redirect(url_for("loan"))
    
    else:
        # GET request: Fetch available devices
        c.execute("SELECT id, rubric_id, suffix_id, category FROM devices WHERE available = 1")
        devices = c.fetchall()
        
        # Get all unique categories for filtering buttons
        c.execute("SELECT DISTINCT category FROM devices")
        categories = [row[0] for row in c.fetchall()]

        conn.close()
        return render_template("loan.html", devices=devices, categories=categories)

@app.route("/return", methods=["GET", "POST"])
def return_device():
    conn = get_db_connection()
    c = conn.cursor()
    
    if request.method == "POST":
        student_id = request.form.get("student")
        device_id = request.form.get("device")
        
        try:
            return_time = datetime.now().isoformat()
            
            # Find the active loan and set the return time
            c.execute("UPDATE loans SET return_time = ? WHERE student_id = ? AND device_id = ? AND return_time IS NULL", 
                      (return_time, student_id, device_id))
            
            if c.rowcount == 0:
                flash("Error: Could not find an active loan for this student/device combination.", "error")
                conn.rollback()
                conn.close()
                return redirect(url_for("return_device"))
                
            # Update device availability to 1 (Loanable)
            c.execute("UPDATE devices SET available = 1 WHERE id = ?", (device_id,))
            
            conn.commit()
            flash(f"Device ID {device_id} returned successfully!", "success")
        
        except sqlite3.Error as e:
            flash(f"Database Error: {e}", "error")
            conn.rollback()
            
        conn.close()
        return redirect(url_for("return_device"))
    
    else:
        # GET request: Fetch students who have active loans
        c.execute("""
            SELECT DISTINCT s.id, s.name || ' ' || s.surname 
            FROM students s 
            JOIN loans l ON s.id = l.student_id 
            WHERE l.return_time IS NULL
        """)
        students_with_active_loans = c.fetchall()
        
        # Fetch devices that are currently on loan
        c.execute("""
            SELECT d.id, d.rubric_id || '-' || d.suffix_id || ' (' || d.category || ')' 
            FROM devices d 
            WHERE d.available = 0
        """)
        devices_on_loan = c.fetchall()
        
        conn.close()
        return render_template("return.html", students=students_with_active_loans, devices=devices_on_loan)

@app.route("/admin", methods=["GET", "POST"])
@login_required
def admin():
    conn = get_db_connection()
    c = conn.cursor()
    
    if request.method == "POST":
        # --- Handle Active Device Return (NEW LOGIC) ---
        active_return_id_full = request.form.get("active_return_id")
        if active_return_id_full:
            try:
                # 1. Split the full ID (e.g., 'SHC-LQ-001') to find the device
                parts = active_return_id_full.split('-')
                if len(parts) >= 3:
                    rubric_id = "-".join(parts[:-1]) # Reconstruct rubric part
                    suffix_id = parts[-1]
                else:
                    raise ValueError("Invalid full device ID format.")

                # 2. Find the Device ID (primary key)
                c.execute("SELECT id FROM devices WHERE rubric_id = ? AND suffix_id = ?", (rubric_id, suffix_id))
                device_row = c.fetchone()
                
                if not device_row:
                    flash(f"Error: Could not find device with ID {active_return_id_full}.", "error")
                    conn.rollback()
                    conn.close()
                    return redirect(url_for("admin"))
                
                device_id = device_row[0]
                return_time = datetime.now().isoformat()
                
                # 3. Find the most recent ACTIVE loan for this device and update the return time
                # We update the loan with return_time IS NULL
                c.execute("""
                    UPDATE loans 
                    SET return_time = ? 
                    WHERE device_id = ? AND return_time IS NULL
                """, (return_time, device_id))
                
                # 4. Update device availability to 1 (Loanable)
                c.execute("UPDATE devices SET available = 1 WHERE id = ?", (device_id,))
                
                conn.commit()
                flash(f"Device {active_return_id_full} marked as handed in successfully!", "success")

            except (sqlite3.Error, ValueError) as e:
                flash(f"Error processing return for {active_return_id_full}: {e}", "error")
                conn.rollback()

            conn.close()
            return redirect(url_for("admin"))


        # --- Handle Device Deletion ---
        delete_id = request.form.get("delete_id")
        if delete_id:
            try:
                # Check if the device is currently on loan
                c.execute("SELECT available FROM devices WHERE id = ?", (delete_id,))
                available_status = c.fetchone()
                
                if available_status is not None and available_status[0] == 0:
                    flash(f"Cannot delete device ID {delete_id}. It is currently on loan.", "error")
                else:
                    c.execute("DELETE FROM devices WHERE id = ?", (delete_id,))
                    conn.commit()
                    flash(f"Device ID {delete_id} deleted successfully!", "success")
            except sqlite3.Error as e:
                flash(f"Error deleting device: {e}", "error")
                conn.rollback()
            conn.close()
            return redirect(url_for("admin"))

        # --- Handle Device Addition ---
        rubric_id = request.form.get("rubric_id")
        suffix_id = request.form.get("suffix_id")
        category = request.form.get("category")
        
        try:
            # New devices are inserted with available = 1 (Loanable)
            c.execute("INSERT INTO devices (rubric_id, suffix_id, category, available) VALUES (?, ?, ?, 1)", 
                      (rubric_id, suffix_id, category))
            conn.commit()
            flash("Device added successfully!", "success")
        except sqlite3.Error as e:
            flash(f"Error adding device: {e}", "error")
            conn.rollback()
        
        conn.close()
        return redirect(url_for("admin"))
    
    else:
        # GET request: Fetch data for display
        
        # 1. Fetch all devices
        c.execute("SELECT * FROM devices ORDER BY id DESC")
        devices = c.fetchall()
        
        # 2. Fetch detailed loan history (all loans, including returned)
        c.execute("""
            SELECT 
                s.name, 
                s.surname, 
                d.rubric_id,
                d.suffix_id,
                l.loan_time, 
                l.return_time
            FROM loans l
            JOIN students s ON l.student_id = s.id
            JOIN devices d ON l.device_id = d.id
            ORDER BY l.loan_time DESC
        """)
        loan_records = c.fetchall()
        
        # Process loan records to format dates and times
        formatted_loans = []
        for name, surname, rubric_id, suffix_id, loan_time_str, return_time_str in loan_records:
            device_full_id = f"{rubric_id}-{suffix_id}"
            
            # Format Loan Time
            try:
                loan_dt = datetime.fromisoformat(loan_time_str)
                loan_date = loan_dt.strftime("%d/%m/%y")
                loan_time = loan_dt.strftime("%H:%M")
            except ValueError:
                loan_date = "Invalid Date"
                loan_time = "Invalid Time"
            
            # Format Return Time (or set to N/A if null)
            return_date = "N/A"
            return_time = "N/A"
            status = "On Loan"
            
            if return_time_str:
                try:
                    return_dt = datetime.fromisoformat(return_time_str)
                    return_date = return_dt.strftime("%d/%m/%y")
                    return_time = return_dt.strftime("%H:%M")
                    status = "Returned"
                except ValueError:
                    return_date = "Invalid Date"
                    return_time = "Invalid Time"

            formatted_loans.append({
                'student_name': f"{name} {surname}",
                'device_id': device_full_id,
                'loan_date': loan_date,
                'loan_time': loan_time,
                'return_date': return_date,
                'return_time': return_time,
                'status': status
            })

        # 3. Fetch Active Loans (New Table Data)
        c.execute("""
            SELECT 
                d.rubric_id,
                d.suffix_id, 
                d.category,
                s.name, 
                s.surname, 
                s.email
            FROM devices d
            JOIN loans l ON d.id = l.device_id
            JOIN students s ON l.student_id = s.id
            WHERE d.available = 0 AND l.return_time IS NULL
            ORDER BY d.category, s.surname
        """)
        devices_on_loan_list = c.fetchall()
        
        # Combine rubric and suffix for display in the template
        devices_on_loan_formatted = []
        for rubric, suffix, category, name, surname, email in devices_on_loan_list:
             devices_on_loan_formatted.append([
                f"{rubric}-{suffix}", # device_full_id [0]
                category,             # category [1]
                name,                 # name [2]
                surname,              # surname [3]
                email                 # email [4]
            ])

        conn.close()
        return render_template("admin.html", 
                               devices=devices, 
                               loans=formatted_loans,
                               devices_on_loan=devices_on_loan_formatted)

if __name__ == "__main__":
    generate_credentials()
    init_db()
    # Ensure sys.path is correct for relative imports in some environments
    if "." not in sys.path:
        sys.path.append(".")
    
    app.run(debug=True)
