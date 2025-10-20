import secrets
import string
import os
from flask import Flask, render_template, request, redirect, url_for, flash, session, make_response, send_file
import sqlite3
from datetime import datetime
import sys
import io
import pandas as pd

app = Flask(__name__)
app.secret_key = secrets.token_hex(24)
DB_FILE = "device_loans.db"

# --- Admin Authentication Setup ---
ADMIN_USERNAME = ""
ADMIN_PASSWORD = ""

def generate_credentials():
    """Generates unique username and password for this app instance."""
    global ADMIN_USERNAME, ADMIN_PASSWORD
    random_suffix = ''.join(secrets.choice(string.digits) for _ in range(4))
    ADMIN_USERNAME = f"admin_{random_suffix}"
    chars = string.ascii_letters + string.digits + "!@#$%^&*"
    ADMIN_PASSWORD = ''.join(secrets.choice(chars) for _ in range(16))

    print("\n" + "="*50)
    print("!!! ADMIN ACCESS CREDENTIALS !!!")
    print(f"USERNAME: {ADMIN_USERNAME}")
    print(f"PASSWORD: {ADMIN_PASSWORD}")
    print("Please use these to log into the /admin panel.")
    print("Credentials are valid ONLY for this session.")
    print("="*50 + "\n")

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS devices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, rubric_id TEXT, suffix_id TEXT,
                    category TEXT, available INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS students (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, surname TEXT, email TEXT UNIQUE)''')
    c.execute('''CREATE TABLE IF NOT EXISTS loans (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER, device_id INTEGER,
                    loan_time TEXT, return_time TEXT,
                    FOREIGN KEY(student_id) REFERENCES students(id),
                    FOREIGN KEY(device_id) REFERENCES devices(id))''')
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
    return sqlite3.connect(DB_FILE)

def format_dt(iso_time_str):
    if not iso_time_str: return "N/A", "N/A"
    try:
        dt = datetime.fromisoformat(iso_time_str)
        return dt.strftime("%d/%m/%y"), dt.strftime("%H:%M")
    except ValueError:
        return "Invalid Date", "Invalid Time"

# --- Routes ---

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['logged_in'] = True
            flash("Logged in successfully!", "success")
            return redirect(url_for("admin"))
        else:
            flash("Invalid credentials. Please try again.", "error")
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
        name, surname, email = request.form.get("name"), request.form.get("surname"), request.form.get("email")
        device_id = request.form.get("selected_device_id")
        if not device_id:
            flash("Please select a device before attempting to loan.", "error")
            conn.close()
            return redirect(url_for("loan"))
        try:
            c.execute("SELECT id FROM students WHERE email = ?", (email,))
            student_row = c.fetchone()
            if student_row:
                student_id = student_row[0]
                c.execute("UPDATE students SET name = ?, surname = ? WHERE id = ?", (name, surname, student_id))
            else:
                c.execute("INSERT INTO students (name, surname, email) VALUES (?, ?, ?)", (name, surname, email))
                student_id = c.lastrowid
            
            c.execute("SELECT available FROM devices WHERE id = ?", (device_id,))
            available_status = c.fetchone()
            if available_status is None or available_status[0] == 0:
                flash("Error: Device is unavailable or does not exist.", "error")
                conn.rollback()
            else:
                loan_time = datetime.now().isoformat()
                c.execute("INSERT INTO loans (student_id, device_id, loan_time) VALUES (?, ?, ?)", (student_id, device_id, loan_time))
                c.execute("UPDATE devices SET available = 0 WHERE id = ?", (device_id,))
                conn.commit()
                flash(f"Device ID {device_id} loaned successfully to {name}!", "success")
        except sqlite3.Error as e:
            flash(f"Database Error: {e}", "error")
            conn.rollback()
        finally:
            conn.close()
        return redirect(url_for("loan"))
    else:
        c.execute("SELECT id, rubric_id, suffix_id, category FROM devices WHERE available = 1")
        devices = c.fetchall()
        c.execute("SELECT DISTINCT category FROM devices")
        categories = [row[0] for row in c.fetchall()]
        conn.close()
        return render_template("loan.html", devices=devices, categories=categories)

@app.route("/return", methods=["GET", "POST"])
def return_device():
    conn = get_db_connection()
    c = conn.cursor()
    if request.method == "POST":
        student_id, device_id = request.form.get("student"), request.form.get("device")
        try:
            return_time = datetime.now().isoformat()
            c.execute("UPDATE loans SET return_time = ? WHERE student_id = ? AND device_id = ? AND return_time IS NULL", 
                        (return_time, student_id, device_id))
            if c.rowcount == 0:
                flash("Error: Could not find an active loan for this student/device combination.", "error")
                conn.rollback()
            else:
                c.execute("UPDATE devices SET available = 1 WHERE id = ?", (device_id,))
                conn.commit()
                flash(f"Device ID {device_id} returned successfully!", "success")
        except sqlite3.Error as e:
            flash(f"Database Error: {e}", "error")
            conn.rollback()
        finally:
            conn.close()
        return redirect(url_for("return_device"))
    else:
        c.execute("SELECT DISTINCT s.id, s.name || ' ' || s.surname FROM students s JOIN loans l ON s.id = l.student_id WHERE l.return_time IS NULL")
        students_with_active_loans = c.fetchall()
        c.execute("SELECT d.id, d.rubric_id || '-' || d.suffix_id || ' (' || d.category || ')' FROM devices d WHERE d.available = 0")
        devices_on_loan = c.fetchall()
        conn.close()
        return render_template("return.html", students=students_with_active_loans, devices=devices_on_loan)

@app.route("/admin", methods=["GET", "POST"])
@login_required
def admin():
    conn = get_db_connection()
    c = conn.cursor()
    if request.method == "POST":
        action_handled = False
        # Handle Active Device Return
        if "active_return_id" in request.form:
            active_return_id_full = request.form.get("active_return_id")
            try:
                parts = active_return_id_full.split('-')
                rubric_id = "-".join(parts[:-1]) if len(parts) > 2 else parts[0]
                suffix_id = parts[-1]
                c.execute("SELECT id FROM devices WHERE rubric_id = ? AND suffix_id = ?", (rubric_id, suffix_id))
                device_row = c.fetchone()
                if not device_row:
                    flash(f"Error: Could not find device with ID {active_return_id_full}.", "error")
                else:
                    device_id = device_row[0]
                    return_time = datetime.now().isoformat()
                    c.execute("UPDATE loans SET return_time = ? WHERE device_id = ? AND return_time IS NULL", (return_time, device_id))
                    c.execute("UPDATE devices SET available = 1 WHERE id = ?", (device_id,))
                    conn.commit()
                    flash(f"Device {active_return_id_full} marked as handed in successfully!", "success")
            except (sqlite3.Error, ValueError) as e:
                flash(f"Error processing return: {e}", "error")
                conn.rollback()
            action_handled = True
        
        # Handle Device Deletion
        if "delete_id" in request.form:
            delete_id = request.form.get("delete_id")
            try:
                c.execute("SELECT available FROM devices WHERE id = ?", (delete_id,))
                status = c.fetchone()
                if status and status[0] == 0:
                    flash(f"Cannot delete device ID {delete_id}. It is currently on loan.", "error")
                else:
                    c.execute("DELETE FROM devices WHERE id = ?", (delete_id,))
                    conn.commit()
                    flash(f"Device ID {delete_id} deleted successfully!", "success")
            except sqlite3.Error as e:
                flash(f"Error deleting device: {e}", "error")
                conn.rollback()
            action_handled = True

        # Handle Device Addition
        if "rubric_id" in request.form and not action_handled:
            rubric_id, suffix_id, category = request.form.get("rubric_id"), request.form.get("suffix_id"), request.form.get("category")
            if rubric_id and suffix_id and category:
                try:
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
        # GET request
        c.execute("SELECT * FROM devices ORDER BY id DESC")
        devices_raw = c.fetchall()
        c.execute("""
            SELECT s.name, s.surname, d.rubric_id, d.suffix_id, l.loan_time, l.return_time
            FROM loans l JOIN students s ON l.student_id = s.id JOIN devices d ON l.device_id = d.id
            ORDER BY l.loan_time DESC
        """)
        loan_records = c.fetchall()
        formatted_loans = [{
            'student_name': f"{rec[0]} {rec[1]}", 'device_id': f"{rec[2]}-{rec[3]}",
            'loan_date': format_dt(rec[4])[0], 'loan_time': format_dt(rec[4])[1],
            'return_date': format_dt(rec[5])[0], 'return_time': format_dt(rec[5])[1],
            'status': "Returned" if rec[5] else "On Loan"
        } for rec in loan_records]
        
        c.execute("""
            SELECT d.rubric_id, d.suffix_id, d.category, s.name, s.surname, s.email
            FROM devices d JOIN loans l ON d.id = l.device_id JOIN students s ON l.student_id = s.id
            WHERE d.available = 0 AND l.return_time IS NULL ORDER BY d.category, s.surname
        """)
        devices_on_loan_list = c.fetchall()
        devices_on_loan_formatted = [[f"{rec[0]}-{rec[1]}", rec[2], rec[3], rec[4], rec[5]] for rec in devices_on_loan_list]
        
        conn.close()
        return render_template("admin.html", devices=devices_raw, loans=formatted_loans, devices_on_loan=devices_on_loan_formatted)

@app.route("/export_admin_data")
@login_required
def export_admin_data():
    """Exports data as an Excel (.xlsx) file with three sheets."""
    conn = get_db_connection()
    output = io.BytesIO()
    try:
        # Fetch data for all three sheets
        df_on_loan = pd.read_sql_query("""
            SELECT d.rubric_id || '-' || d.suffix_id AS 'Device ID', d.category AS 'Category', 
                   s.name || ' ' || s.surname AS 'Student Name', s.email AS 'Student Email'
            FROM devices d JOIN loans l ON d.id = l.device_id JOIN students s ON l.student_id = s.id
            WHERE d.available = 0 AND l.return_time IS NULL ORDER BY d.category, s.surname
        """, conn)
        df_inventory = pd.read_sql_query("""
            SELECT id AS 'Database ID', rubric_id AS 'Rubric ID', suffix_id AS 'Suffix ID', category AS 'Category',
                   CASE WHEN available = 1 THEN 'Loanable' ELSE 'Loaned Out' END AS 'Status'
            FROM devices ORDER BY id DESC
        """, conn)
        df_history = pd.read_sql_query("""
            SELECT s.name || ' ' || s.surname AS 'Student Name', d.rubric_id || '-' || d.suffix_id AS 'Device ID', d.category,
                   l.loan_time, l.return_time
            FROM loans l JOIN students s ON l.student_id = s.id JOIN devices d ON l.device_id = d.id
            ORDER BY l.loan_time DESC
        """, conn)

        # Format dates in history DataFrame
        df_history[['Loan Date', 'Loan Time']] = df_history['loan_time'].apply(lambda x: pd.Series(format_dt(x)))
        df_history[['Return Date', 'Return Time']] = df_history['return_time'].apply(lambda x: pd.Series(format_dt(x)))
        df_history['Status'] = df_history['return_time'].apply(lambda x: 'Returned' if x else 'On Loan')
        df_history = df_history.drop(columns=['loan_time', 'return_time'])

        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_on_loan.to_excel(writer, sheet_name='Devices On Loan', index=False)
            df_inventory.to_excel(writer, sheet_name='Current Inventory', index=False)
            df_history.to_excel(writer, sheet_name='Loan History', index=False)
        
        output.seek(0)
        filename = f"DeviceLoanReport_{datetime.now().strftime('%d%m%Y')}.xlsx"
        return send_file(output, as_attachment=True, download_name=filename, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

    except Exception as e:
        flash(f"Error exporting Excel file: {e}. You may need to install 'openpyxl'.", "error")
        return redirect(url_for("admin"))
    finally:
        conn.close()

@app.route("/export_db")
@login_required
def export_db():
    """Exports the entire SQLite database file."""
    try:
        filename = f"DeviceLoanBackup_{datetime.now().strftime('%d%m%Y')}.db"
        return send_file(DB_FILE, as_attachment=True, download_name=filename, mimetype='application/x-sqlite3')
    except Exception as e:
        flash(f"Error exporting database file: {e}", "error")
        return redirect(url_for("admin"))

@app.route("/import_admin_data", methods=["POST"])
@login_required
def import_admin_data():
    """Handles the upload of a .db backup file to overwrite the current database."""
    if 'backup_file' not in request.files or not request.files['backup_file'].filename:
        flash("No file selected for import.", "error")
        return redirect(url_for("admin"))
    
    file = request.files['backup_file']
    if not file.filename.endswith('.db'):
        flash("Invalid file type. Please upload a .db file.", "error")
        return redirect(url_for("admin"))
    
    try:
        file.save(DB_FILE)
        flash("Database successfully imported. All previous data has been replaced.", "success")
    except Exception as e:
        flash(f"Error saving database file: {e}. The database was not changed.", "error")
    
    return redirect(url_for("admin"))

if __name__ == "__main__":
    generate_credentials()
    init_db()
    if "." not in sys.path:
        sys.path.append(".")
    app.run(debug=True)

