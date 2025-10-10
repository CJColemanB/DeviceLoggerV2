from flask import Flask, render_template, request, redirect, url_for, session, send_file, flash
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
from io import BytesIO
from fpdf import FPDF
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)
app.secret_key = "supersecretkey"
DB_NAME = "devices.db"

def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        # Create users table
        conn.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT,
            device_code TEXT,
            device_type TEXT,
            date_taken TEXT
        )''')

        # Create devices table
        conn.execute('''CREATE TABLE IF NOT EXISTS devices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_code TEXT UNIQUE,
            device_type TEXT,
            status TEXT DEFAULT 'available'
        )''')

        # Pre-populate devices if empty
        existing = conn.execute("SELECT COUNT(*) FROM devices").fetchone()[0]
        if existing == 0:
            devices = [
                ('LAP001', 'Laptop'),
                ('LAP002', 'Laptop'),
                ('CHG001', 'Laptop Charger'),
                ('HD001', 'Headphones'),
                ('IP001', 'iPad')
            ]
            conn.executemany("INSERT INTO devices (device_code, device_type) VALUES (?, ?)", devices)

@app.route("/", methods=["GET", "POST"])
@app.route("/", methods=["GET", "POST"])
def home():
    with sqlite3.connect(DB_NAME) as conn:
        available_devices = conn.execute(
            "SELECT device_code, device_type FROM devices WHERE status='available'"
        ).fetchall()

    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        device_code = request.form["device_code"]
        device_type = request.form["device_type"]
        date_taken = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with sqlite3.connect(DB_NAME) as conn:
            conn.execute(
                "INSERT INTO users (name, email, device_code, device_type, date_taken) VALUES (?, ?, ?, ?, ?)",
                (name, email, device_code, device_type, date_taken)
            )
            conn.execute("UPDATE devices SET status='loaned' WHERE device_code=?", (device_code,))
        flash("Device loan recorded successfully!", "success")
        return redirect(url_for("home"))

    return render_template("home.html", available_devices=available_devices)

@app.route("/signout", methods=["GET", "POST"])
def signout():
    with sqlite3.connect(DB_NAME) as conn:
        users = conn.execute("SELECT name, device_code FROM users").fetchall()

    if request.method == "POST":
        selected_name = request.form["name"]
        selected_device = request.form["device_code"]
        with sqlite3.connect(DB_NAME) as conn:
            conn.execute("DELETE FROM users WHERE name=? AND device_code=?", (selected_name, selected_device))
            conn.execute("UPDATE devices SET status='available' WHERE device_code=?", (selected_device,))
        flash(f"{selected_name} has signed out successfully.", "success")
        return redirect(url_for("home"))

    return render_template("signout.html", users=users)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if username == "admin" and password == "password123":
            session["admin"] = True
            return redirect(url_for("admin"))
        else:
            flash("Invalid credentials", "danger")
    return render_template("login.html")

@app.route("/admin")
def admin():
    if not session.get("admin"):
        return redirect(url_for("login"))
    with sqlite3.connect(DB_NAME) as conn:
        data = conn.execute("SELECT * FROM users").fetchall()
    return render_template("admin.html", data=data)

@app.route("/export/excel")
def export_excel():
    if not session.get("admin"):
        return redirect(url_for("login"))
    with sqlite3.connect(DB_NAME) as conn:
        df = pd.read_sql_query("SELECT * FROM users", conn)
    output = BytesIO()
    df.to_excel(output, index=False)
    output.seek(0)
    return send_file(output, download_name="devices.xlsx", as_attachment=True)

@app.route("/export/pdf")
def export_pdf():
    if not session.get("admin"):
        return redirect(url_for("login"))
    with sqlite3.connect(DB_NAME) as conn:
        data = conn.execute("SELECT * FROM users").fetchall()
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Device Loan Report", ln=True, align="C")
    pdf.ln(10)
    for row in data:
        pdf.cell(200, 10, txt=str(row), ln=True)
    output = BytesIO()
    pdf.output(output)
    output.seek(0)
    return send_file(output, download_name="devices.pdf", as_attachment=True)

@app.route("/email-overdue")
def email_overdue():
    if not session.get("admin"):
        return redirect(url_for("login"))
    overdue_days = 7
    cutoff_date = datetime.now() - timedelta(days=overdue_days)
    with sqlite3.connect(DB_NAME) as conn:
        overdue_users = conn.execute("SELECT name, email, device_code, date_taken FROM users").fetchall()
    overdue_list = [u for u in overdue_users if datetime.strptime(u[3], "%Y-%m-%d %H:%M:%S") < cutoff_date]
    if not overdue_list:
        flash("No overdue devices found.", "info")
        return redirect(url_for("admin"))
    sender_email = "your_email@example.com"
    sender_password = "your_email_password"
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        for user in overdue_list:
            name, email, device_code, date_taken = user
            subject = "Overdue Device Reminder"
            body = f"Dear {name},\n\nYour device ({device_code}) is overdue. Please return it as soon as possible.\n\nThank you."
            msg = MIMEMultipart()
            msg["From"] = sender_email
            msg["To"] = email
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "plain"))
            server.sendmail(sender_email, email, msg.as_string())
        server.quit()
        flash("Emails sent to all overdue users.", "success")
    except Exception as e:
        flash(f"Error sending emails: {e}", "danger")
    return redirect(url_for("admin"))

@app.route("/logout")
def logout():
    session.pop("admin", None)
    return redirect(url_for("login"))

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
