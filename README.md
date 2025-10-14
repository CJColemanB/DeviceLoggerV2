# 💻 Device Loan Management System

This is a simple, browser-based web application built with **Python (Flask)** and **SQLite** for managing the loan and return of devices (Laptops, iPads, etc.) within a school or organization.

## ✨ Key Features
- **Easy Device Loans**: Quickly check out devices to students, tracking their name, surname, and email.
- **Real-time Inventory**: Devices are marked as Loanable or Loaned Out instantly.
- **Admin Panel (Secured)**: Dedicated section for adding/deleting devices and viewing all historical and active loan data.
- **Automated Time Stamping**: All loans and returns are automatically recorded with specific date (DD/MM/YY) and time (HH:MM) stamps.
- **Quick Return Action**: Administrators can mark a device as returned directly from the active loan list.

## 📁 File Structure
File/FolderDescriptionapp.pyThe main Flask application containing all routing, database (SQLite) connection, and loan logic.| `device_loans.db` | The SQLite database file (created automatically on first run) that stores all device, student, and loan data. |
| `templates/`      | Directory for HTML templates. |
| &nbsp;&nbsp;├── `index.html` | The main landing page. |
| &nbsp;&nbsp;├── `loan.html`  | Page for loaning a device. |
| &nbsp;&nbsp;├── `return.html`| Page for returning a device using student/device dropdowns. |
| &nbsp;&nbsp;├── `login.html` | Admin login page. |
| &nbsp;&nbsp;└── `admin.html` | The main Admin Dashboard with inventory and history. |
| `static/`         | Directory for supporting assets. |
| &nbsp;&nbsp;├── `styles.css` | Custom styles for buttons and tables. |
| &nbsp;&nbsp;└── `loan.js`    | JavaScript for handling device selection and filtering on the loan page. |

## 🚀 Getting Started
### Prerequisites
You need **Python 3** installed to run the Flask application.

### 1. Run the Application
Make sure all files are in the same directory.

Open your terminal or command prompt in that directory.

Run the application using the following command:


python app.py
