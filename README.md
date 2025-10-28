# 💻 Device Loan Management System

A robust, browser-based web application for managing the loan and return of devices (e.g., laptops, iPads) within a school or organization. Built with **Python (Flask)** and **SQLite** for simplicity, reliability, and ease of deployment.

---

## ✨ Features

- **Effortless Device Loans:** Quickly check out devices to students, with fields for name, surname, and email.
- **Real-Time Inventory Status:** Instantly see which devices are available or currently loaned out.
- **Secure Admin Panel:** Access a protected dashboard to add/remove devices, and view both active and historical loan data.
- **Automated Timestamping:** All loans and returns are accurately recorded with date (`DD/MM/YY`) and time (`HH:MM`) stamps.
- **One-Click Returns:** Admins can mark devices as returned directly from the active loan list.
- **Simple Exporting Tools:** Admins can easily export and import the database used, as well as export as an xlsx file, allowing for easy viewing of data

---

## 📁 File Structure

| File/Folder        | Description                                                                 |
|--------------------|-----------------------------------------------------------------------------|
| `app.py`           | Main Flask application with routing, database connections, and loan logic.   |
| `device_loans.db`  | SQLite database file (auto-created). Stores device, student, and loan data.  |
| `templates/`       | HTML templates for all pages.                                                |
| &nbsp;&nbsp;├── `index.html`   | Home/landing page.                              |
| &nbsp;&nbsp;├── `loan.html`    | Device loan form and selection.                  |
| &nbsp;&nbsp;├── `return.html`  | Return devices, now uses cards instead of a dropdown for ease of viewing for users.             |
| &nbsp;&nbsp;├── `login.html`   | Admin login page.                               |
| &nbsp;&nbsp;└── `admin.html`   | Admin dashboard with inventory/history.          |
| `static/`          | Static assets (CSS, JS).                                                    |
| &nbsp;&nbsp;├── `styles.css`   | Custom styles for UI elements.                   |
| &nbsp;&nbsp;└── `loan.js`      | JS for device selection/filtering on loan page.  |
| &nbsp;&nbsp;└── `admin.js`      | JS for all technical usage for admin.js that isn't handled by the app.py.  |

---

## 🚀 Getting Started

### Prerequisites

- **Python 3** installed on your system.
- **Flask** installed on your system.
- **Pandas** installed on your system.
- **OpenPyXL** installed on your system.
- **Setup your environment** by doing the following:
   - Install [Python]([url](https://www.python.org/downloads/)) for your device
   - Install Python3 by typing ```python3``` into your terminal
   - Open your terminal or cmd application
   - install the libraries:
     ```bash
     python3 -m pip install --upgrade pip
     pip install flask
     pip install pandas
     pip install openpyxl
     ```

### 1.1 Running the Application via GitHub Codespaces

1. Ensure all files are in the same directory.
2. Open your terminal or command prompt in that directory.
3. Start the application:
   ```bash
   python3 app.py
   ```
#### 1.2: Running the Application Locally

1. From the repository page, click "code", then "local", then "download ZIP"
2. Unzip the package
3. Open your terminal, then direct to the unzipped package's directory, for example
    ```bash
    cd C:\Users\[user]\Downloads\DeviceLoggerV2\DeviceLoggerV2
    ```
5. start the application:
   ```bash
   python3 app.py
   ```
### 2. Admin Access Credentials

- Upon starting `app.py`, unique admin credentials (username and password) are generated and displayed in the terminal:
  ```
  ================================================== 
  !!! ADMIN ACCESS CREDENTIALS !!! 
  USERNAME: admin_xxxx 
  PASSWORD: [a complex string] 
  Please use these to log into the /admin panel. 
  Credentials are valid ONLY for this session. 
  ================================================== 
  ```

### 3. Using the Website

- **Home Page (`/`):** Main navigation for Loan, Return, and Admin functions.
- **Loan Device (`/loan`):**
  - Fill student details (Name, Surname, Email).
  - Filter available devices by category.
  - Select a device and click "Loan Device".
- **Return Device Page (`/return`):**
  - Users can select from all of the devices currently on loan, and select one to return.
  - all data regarding actually returning the device is hidden from the user and done via the admin side, which administrators can see via the Admin Panel.
- **Admin Panel (`/admin`):**
  - Log in with generated credentials.
  - Add new devices (category, rubric, suffix).
  - View active loans and mark devices as returned.
  - Review full loan history with timestamps.

---

## 🛠️ Technical Details

### Database Schema

The system uses three main tables:

- **devices:** Inventory (rubric_id, suffix_id, category, availability).
- **students:** Borrower information (name, surname, email).
- **loans:** Links students and devices per transaction; records loan and return timestamps.

### Device Return Logic (Admin Panel)

When "Mark as Handed In" is clicked in the Admin Panel, `app.py` processes the device ID, locates the device, and sets the `return_time` for the active loan entry. The device status is updated to available in real time.

---

## 📄 License

This project is provided for educational and internal organizational use. For commercial deployment or redistribution, please review licensing requirements.

---

## 🤝 Contributing

Contributions and feedback are welcome! Please open an issue or submit a pull request for improvements, bug fixes, or feature suggestions.

---

## 📧 Support

For help or questions, please contact the repository maintainer via GitHub Issues.
