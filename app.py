
from flask import Flask, render_template, request, redirect
import sqlite3
import os
import random
import string
from datetime import datetime

app = Flask(__name__)
DB_NAME = 'device_loans.db'

# Generate random admin credentials
admin_username = ''.join(random.choices(string.ascii_letters, k=8))
admin_password = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
print(f"Admin credentials - Username: {admin_username}, Password: {admin_password}")

# Initialize database
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS loans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            surname TEXT,
            email TEXT,
            device_type TEXT,
            device_id TEXT,
            on_loan BOOLEAN,
            loan_time TEXT,
            return_time TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS admin_logins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            login_time TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/loan', methods=['GET', 'POST'])
def loan():
    if request.method == 'POST':
        name = request.form['name']
        surname = request.form['surname']
        email = request.form['email']
        device_type = request.form['device_type']
        device_id = request.form['device_id']
        loan_time = datetime.now().isoformat()
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('''
            INSERT INTO loans (name, surname, email, device_type, device_id, on_loan, loan_time)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (name, surname, email, device_type, device_id, True, loan_time))
        conn.commit()
        conn.close()
        return redirect('/')
    return render_template('loan.html')

@app.route('/return', methods=['GET', 'POST'])
def return_device():
    if request.method == 'POST':
        name = request.form['name']
        device_ids = request.form.getlist('device_id')
        return_time = datetime.now().isoformat()
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        for device_id in device_ids:
            c.execute('''
                UPDATE loans SET on_loan = ?, return_time = ?
                WHERE name = ? AND device_id = ?
            ''', (False, return_time, name, device_id))
        conn.commit()
        conn.close()
        return redirect('/')
    return render_template('return.html')

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == admin_username and password == admin_password:
            login_time = datetime.now().isoformat()
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute('INSERT INTO admin_logins (username, login_time) VALUES (?, ?)', (username, login_time))
            conn.commit()
            conn.close()
            return "Admin logged in successfully."
        else:
            return "Invalid credentials."
    return render_template('admin.html')

if __name__ == '__main__':
    app.run(debug=True)
