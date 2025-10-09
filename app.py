from flask import Flask, render_template, request, redirect, url_for, send_file
from flask_sqlalchemy import SQLAlchemy
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import csv

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///loan_system.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Device(db.Model):
    id = db.Column(db.String, primary_key=True)
    type = db.Column(db.String, nullable=False)
    available = db.Column(db.Boolean, default=True)

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String, nullable=False)
    email = db.Column(db.String, nullable=False)

class Loan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    device_id = db.Column(db.String, db.ForeignKey('device.id'), nullable=False)
    loan_date = db.Column(db.String, nullable=False)
    return_date = db.Column(db.String)

db.create_all()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/loan', methods=['GET', 'POST'])
def loan():
    if request.method == 'POST':
        full_name = request.form['full_name']
        email = request.form['email']
        device_ids = request.form.getlist('device_ids')
        student = Student(full_name=full_name, email=email)
        db.session.add(student)
        db.session.commit()
        for device_id in device_ids:
            loan = Loan(student_id=student.id, device_id=device_id, loan_date=datetime.now().strftime("%Y-%m-%d %H:%M"))
            db.session.add(loan)
            device = Device.query.get(device_id)
            device.available = False
        db.session.commit()
        return redirect(url_for('index'))
    devices = Device.query.filter_by(available=True).all()
    return render_template('loan.html', devices=devices)

@app.route('/return', methods=['GET', 'POST'])
def return_device():
    if request.method == 'POST':
        student_id = request.form['student_id']
        loans = Loan.query.filter_by(student_id=student_id, return_date=None).all()
        for loan in loans:
            loan.return_date = datetime.now().strftime("%Y-%m-%d %H:%M")
            device = Device.query.get(loan.device_id)
            device.available = True
        db.session.commit()
        return redirect(url_for('index'))
    students = Student.query.all()
    return render_template('return.html', students=students)

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        device_id = request.form['device_id']
        device_type = request.form['device_type']
        available = True if request.form.get('available') == 'on' else False
        device = Device(id=device_id, type=device_type, available=available)
        db.session.add(device)
        db.session.commit()
        return redirect(url_for('admin'))
    return render_template('admin.html')

def generate_report():
    loans = Loan.query.filter_by(return_date=None).all()
    with open('daily_report.csv', 'w', newline='') as csvfile:
        fieldnames = ['Student Name', 'Email', 'Device ID', 'Device Type', 'Loan Date']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for loan in loans:
            student = Student.query.get(loan.student_id)
            device = Device.query.get(loan.device_id)
            writer.writerow({
                'Student Name': student.full_name,
                'Email': student.email,
                'Device ID': device.id,
                'Device Type': device.type,
                'Loan Date': loan.loan_date
            })

@app.route('/download_report')
def download_report():
    generate_report()
    return send_file('daily_report.csv', as_attachment=True)

scheduler = BackgroundScheduler()
scheduler.add_job(func=generate_report, trigger='cron', hour=16, minute=0)
scheduler.start()

if __name__ == '__main__':
    app.run(debug=True)
