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
                    category TEXT, available INTEGER,
                    UNIQUE(rubric_id, suffix_id))''')
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
        name = request.form.get("name")
        surname = request.form.get("surname")
        email = request.form.get("email")
        # Get the comma-separated string from the hidden input
        device_ids_str = request.form.get("selected_device_ids") 

        # --- DATA INTEGRITY CHECKS ---
        if not email or not email.lower().endswith("gdst.net"):
            flash("Invalid email address. Please use a valid GDST email.", "error")
            conn.close()
            return redirect(url_for("loan"))
        
        if not device_ids_str:
            flash("Please select at least one device before attempting to loan.", "error")
            conn.close()
            return redirect(url_for("loan"))

        device_ids = [d_id.strip() for d_id in device_ids_str.split(',') if d_id.strip()]

        try:
            # 1. Handle Student Record (Only do this once)
            c.execute("SELECT id FROM students WHERE email = ?", (email,))
            student_row = c.fetchone()
            if student_row:
                student_id = student_row[0]
                c.execute("UPDATE students SET name = ?, surname = ? WHERE id = ?", (name, surname, student_id))
            else:
                c.execute("INSERT INTO students (name, surname, email) VALUES (?, ?, ?)", (name, surname, email))
                student_id = c.lastrowid

            loaned_successfully = []
            
            # 2. Loop through each selected device
            for d_id in device_ids:
                # Check if this specific device is still available
                c.execute("SELECT available, rubric_id, suffix_id FROM devices WHERE id = ?", (d_id,))
                device_info = c.fetchone()

                if device_info and device_info[0] == 1:
                    loan_time = datetime.now().isoformat()
                    # Create Loan record
                    c.execute("INSERT INTO loans (student_id, device_id, loan_time) VALUES (?, ?, ?)", 
                              (student_id, d_id, loan_time))
                    # Mark device as loaned out
                    c.execute("UPDATE devices SET available = 0 WHERE id = ?", (d_id,))
                    
                    # Track for the final success message
                    full_id = f"{device_info[1]}{device_info[2]}"
                    loaned_successfully.append(full_id)
                else:
                    flash(f"Warning: Device {d_id} was already taken or doesn't exist. Skipping.", "error")

            # 3. Finalize
            if loaned_successfully:
                conn.commit()
                devices_list = ", ".join(loaned_successfully)
                flash(f"Successfully loaned: {devices_list} to {name}!", "success")
            else:
                conn.rollback()
                flash("No devices were loaned. Please try again.", "error")

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
        loan_id = request.form.get("loan_id")
        category_filter = request.form.get('category_filter') # Read filter from hidden form field
        try:
            c.execute("SELECT device_id FROM loans WHERE id = ?", (loan_id,))
            loan_info = c.fetchone()
            if not loan_info:
                flash("Error: Could not find the specified loan.", "error")
                conn.rollback()
            else:
                device_id = loan_info[0]
                return_time = datetime.now().isoformat()
                c.execute("UPDATE loans SET return_time = ? WHERE id = ?", (return_time, loan_id))
                c.execute("UPDATE devices SET available = 1 WHERE id = ?", (device_id,))
                conn.commit()
                flash(f"Device returned successfully!", "success")
        except sqlite3.Error as e:
            flash(f"Database Error: {e}", "error")
            conn.rollback()
        finally:
            conn.close()

        if category_filter:
            return redirect(url_for("return_device", category=category_filter))
        return redirect(url_for("return_device"))
    else:
        category_filter = request.args.get('category', None)
        query = """
            SELECT l.id, d.rubric_id, d.suffix_id, s.name, s.surname, d.category
            FROM loans l
            JOIN devices d ON l.device_id = d.id
            JOIN students s ON l.student_id = s.id
            WHERE l.return_time IS NULL
        """
        params = []
        if category_filter:
            query += " AND d.category = ?"
            params.append(category_filter)

        query += " ORDER BY s.surname, s.name"
        c.execute(query, tuple(params))
        active_loans = c.fetchall()
        c.execute("""
            SELECT DISTINCT d.category
            FROM devices d
            JOIN loans l ON d.id = l.device_id
            WHERE l.return_time IS NULL
            ORDER BY d.category
        """)
        loaned_categories = [row[0] for row in c.fetchall()]

        conn.close()
        return render_template("return.html", 
                               active_loans=active_loans, 
                               categories=loaned_categories, 
                               active_category=category_filter)


@app.route("/admin", methods=["GET", "POST"])
@login_required
def admin():
    conn = get_db_connection()
    c = conn.cursor()
    if request.method == "POST":
        action_handled = False
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

        if "rubric_id" in request.form and not action_handled:
            rubric_id, suffix_id, category = request.form.get("rubric_id"), request.form.get("suffix_id"), request.form.get("category")
            if rubric_id and suffix_id and category:
                c.execute("SELECT id FROM devices WHERE rubric_id = ? AND suffix_id = ?", (rubric_id, suffix_id))
                if c.fetchone():
                    flash(f"Error: A device with the ID '{rubric_id}-{suffix_id}' already exists.", "error")
                else:
                    try:
                        c.execute("INSERT INTO devices (rubric_id, suffix_id, category, available) VALUES (?, ?, ?, 1)", (rubric_id, suffix_id, category))
                        conn.commit()
                        flash("Device added successfully!", "success")
                    except sqlite3.Error as e:
                        conn.rollback()
                        flash(f"Error adding device: {e}", "error")
        
        conn.close()
        return redirect(url_for("admin"))
    else:
        sort_by = request.args.get('sort_by', 'id') 
        sort_dir = request.args.get('sort_dir', 'desc')
        if sort_dir.lower() not in ['asc', 'desc']: sort_dir = 'desc'

        inventory_sort_cols = {'id': 'id', 'rubric_id': 'rubric_id', 'suffix_id': 'suffix_id', 'category': 'category', 'available': 'available'}
        on_loan_sort_cols = {'device_id_loan': 'd.rubric_id', 'category_loan': 'd.category', 'student_name_loan': 's.surname', 'student_email_loan': 's.email'}
        history_sort_cols = {'student_name_history': 's.surname', 'device_id_history': 'd.rubric_id', 'loan_time_history': 'l.loan_time', 'return_time_history': 'l.return_time', 'status_history': 'l.return_time IS NULL'}

        inventory_order_by, on_loan_order_by, history_order_by = "ORDER BY id DESC", "ORDER BY d.category, s.surname", "ORDER BY l.loan_time DESC"

        if sort_by in inventory_sort_cols:
            inventory_order_by = f"ORDER BY {inventory_sort_cols[sort_by]} {sort_dir.upper()}"
        elif sort_by in on_loan_sort_cols:
            sql_col = on_loan_sort_cols[sort_by]
            if sort_by == 'student_name_loan': on_loan_order_by = f"ORDER BY s.surname {sort_dir.upper()}, s.name {sort_dir.upper()}"
            elif sort_by == 'device_id_loan': on_loan_order_by = f"ORDER BY d.rubric_id {sort_dir.upper()}, d.suffix_id {sort_dir.upper()}"
            else: on_loan_order_by = f"ORDER BY {sql_col} {sort_dir.upper()}"
        elif sort_by in history_sort_cols:
            sql_col = history_sort_cols[sort_by]
            if sort_by == 'student_name_history': history_order_by = f"ORDER BY s.surname {sort_dir.upper()}, s.name {sort_dir.upper()}"
            elif sort_by == 'device_id_history': history_order_by = f"ORDER BY d.rubric_id {sort_dir.upper()}, d.suffix_id {sort_dir.upper()}"
            else: history_order_by = f"ORDER BY {sql_col} {sort_dir.upper()}"

        c.execute(f"SELECT * FROM devices {inventory_order_by}")
        devices_raw = c.fetchall()
        
        c.execute(f"SELECT s.name, s.surname, d.rubric_id, d.suffix_id, l.loan_time, l.return_time FROM loans l JOIN students s ON l.student_id = s.id JOIN devices d ON l.device_id = d.id {history_order_by}")
        loan_records = c.fetchall()
        
        c.execute(f"SELECT d.rubric_id, d.suffix_id, d.category, s.name, s.surname, s.email FROM devices d JOIN loans l ON d.id = l.device_id JOIN students s ON l.student_id = s.id WHERE d.available = 0 AND l.return_time IS NULL {on_loan_order_by}")
        devices_on_loan_list = c.fetchall()
        
        formatted_loans = [{'student_name': f"{r[0]} {r[1]}", 'device_id': f"{r[2]}-{r[3]}", 'loan_date': format_dt(r[4])[0], 'loan_time': format_dt(r[4])[1], 'return_date': format_dt(r[5])[0], 'return_time': format_dt(r[5])[1], 'status': "Returned" if r[5] else "On Loan"} for r in loan_records]
        devices_on_loan_formatted = [[f"{r[0]}-{r[1]}", r[2], r[3], r[4], r[5]] for r in devices_on_loan_list]
        
        conn.close()
        return render_template("admin.html", devices=devices_raw, loans=formatted_loans, devices_on_loan=devices_on_loan_formatted, sort_by=sort_by, sort_dir=sort_dir)

@app.route("/export_admin_data")
@login_required
def export_admin_data():
    conn = get_db_connection()
    output = io.BytesIO()
    try:
        df_on_loan = pd.read_sql_query("SELECT d.rubric_id || '-' || d.suffix_id AS 'Device ID', d.category AS 'Category', s.name || ' ' || s.surname AS 'Student Name', s.email AS 'Student Email' FROM devices d JOIN loans l ON d.id = l.device_id JOIN students s ON l.student_id = s.id WHERE d.available = 0 AND l.return_time IS NULL ORDER BY d.category, s.surname", conn)
        df_inventory = pd.read_sql_query("SELECT id AS 'Database ID', rubric_id AS 'Rubric ID', suffix_id AS 'Suffix ID', category AS 'Category', CASE WHEN available = 1 THEN 'Loanable' ELSE 'Loaned Out' END AS 'Status' FROM devices ORDER BY id DESC", conn)
        df_history = pd.read_sql_query("SELECT s.name || ' ' || s.surname AS 'Student Name', d.rubric_id || '-' || d.suffix_id AS 'Device ID', d.category, l.loan_time, l.return_time FROM loans l JOIN students s ON l.student_id = s.id JOIN devices d ON l.device_id = d.id ORDER BY l.loan_time DESC", conn)

        df_history[['Loan Date', 'Loan Time']] = df_history['loan_time'].apply(lambda x: pd.Series(format_dt(x)))
        df_history[['Return Date', 'Return Time']] = df_history['return_time'].apply(lambda x: pd.Series(format_dt(x)))
        df_history['Status'] = df_history['return_time'].apply(lambda x: 'Returned' if x else 'On Loan')
        df_history.drop(columns=['loan_time', 'return_time'], inplace=True)

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
    try:
        filename = f"DeviceLoanBackup_{datetime.now().strftime('%d%m%Y')}.db"
        return send_file(DB_FILE, as_attachment=True, download_name=filename, mimetype='application/x-sqlite3')
    except Exception as e:
        flash(f"Error exporting database file: {e}", "error")
        return redirect(url_for("admin"))

@app.route("/import_admin_data", methods=["POST"])
@login_required
def import_admin_data():
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