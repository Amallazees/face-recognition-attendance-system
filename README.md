<h1 align="center"><b>🎓 FACE RECOGNITION ATTENDANCE SYSTEM</b></h1>

A modern, desktop-based Face Recognition Attendance System built with **Python**, **CustomTkinter**, **OpenCV**, **ReportLab**, and **Google Sheets API**. Designed specifically for schools, colleges, and corporate offices to manage attendance seamlessly online and offline.

---

## 🔑 Default Admin Password
- Default Password for **Office Use Only**: **`Amal@123`**
*(Can be updated anytime via the 🔑 **Reset Password** screen).*

---

## 🌟 Features & Highlights

### 1. 📷 Mark Attendance (Live Camera Scanner)
- **Real-Time Detection & Recognition**: Scans webcam feed in real-time using OpenCV, detecting face locations and matching against registered students/employees.
- **Visual Feedback Bounding Boxes**: Displays green bounding box overlay with Student Name, Admission No, and Confidence Score.
- **Instant Cloud & Offline Logging**:
  - Automatically appends log to **Google Sheets** (if connected).
  - Automatically appends local log to `data/attendance.csv`.
- **Duplicate Prevention**: Intelligently prevents duplicate attendance marking for the same student on the same day.

### 2. 🔒 Office Use Only (Password Protected Admin Center)
- **Password Protected**: Accessible using the admin password (Default: **`Amal@123`**).
- **Sub-Switch 1: Upload Students**
  - Live webcam preview with face bounding box detection.
  - One-click snapshot capture or image file selection.
  - Input fields: **Full Name**, **Admission No**, **Roll No**, **Department / Class**.
  - Automatically updates student database (`data/students.json`) and trains the face recognition engine.
- **Sub-Switch 2: Edit Student**
  - Searchable student directory by Name, Admission No, Roll No, or Department.
  - Edit profile information or delete student records with automated face photo cleanup.
- **Sub-Switch 3: View Attendance Details**
  - Interactive data sheet displaying all historical attendance logs (Date, Time, Admission No, Name, Roll No, Department, Status).
  - Live search filter by Name, Admission No, or Department.
  - **📄 Download as PDF Button** (Located at top-right corner of the data sheet): Exports clean, formatted PDF reports.

### 3. 🔑 Reset Password
- Security feature to update admin password.
- Requires **Current Password**, **New Password**, and **Confirm New Password**.
- Securely saves SHA-256 hashed passwords in `data/config.json`.

---

## 🛠️ Tech Stack & Dependencies

- **Programming Language**: Python 3.12+
- **GUI Framework**: CustomTkinter & Tkinter
- **Computer Vision**: OpenCV (`cv2`) & Pillow (`PIL`)
- **PDF Generation**: ReportLab
- **Cloud Database**: Google Sheets API (`gspread` & Google Apps Script Webhook)
- **Data Persistence**: JSON & CSV

---

## 🚀 Quick Start Guide

### Running the Application:
Double-click **`run_attendance_system.bat`** OR run via terminal:
```bash
python app.py
```

---

## 🌐 Google Sheets Sync Setup

1. Open your Google Sheet in a browser (e.g., `https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit`).
2. Go to **Extensions** ➔ **Apps Script** and paste the following Google Apps Script code:
```javascript
function doPost(e) {
  var data = JSON.parse(e.postData.contents);
  var sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
  
  if (sheet.getLastRow() === 0) {
    sheet.appendRow(["Date", "Time", "Admission No", "Name", "Roll No", "Department", "Status"]);
  }
  
  sheet.appendRow([
    data.date,
    data.time,
    data.admission_no,
    data.name,
    data.roll_no,
    data.department,
    data.status
  ]);
  
  return ContentService.createTextOutput("Success");
}
```
3. Click **Deploy** ➔ **New deployment** ➔ Type: **Web app** ➔ Who has access: **Anyone** ➔ Copy the Web App URL.
4. Open the app -> Click **`⚙️ Google Sheet Settings`** (bottom right) -> Paste Web App URL -> Click **`🧪 Test Connection`** -> Click **`💾 Save Settings`**.

---

## 📁 Project File Structure

```
├── app.py                      # Main Application Entry Point
├── run_attendance_system.bat   # Windows Batch File Launcher
├── requirements.txt            # Python Dependencies
├── README.md                   # Project Documentation
├── core/
│   ├── face_engine.py          # OpenCV Face Detection & Recognition
│   ├── storage_manager.py      # JSON DB, Password Hash & PDF Generator
│   └── sheets_manager.py       # Google Sheets API & Webhook Manager
├── gui/
│   ├── theme.py                # Styling, Colors & Typography
│   ├── main_window.py          # Main Dashboard Interface
│   ├── office_admin_view.py    # Admin Center (Upload, Edit, Attendance Sheet, PDF Export)
│   ├── attendance_view.py      # Live Camera Attendance Scanner
│   └── password_reset_view.py  # Password Reset Modal
└── data/
    ├── students.json           # Registered Student Profiles
    ├── config.json             # App Configuration & Password Hash
    ├── attendance.csv          # Local Attendance Log
    └── faces/                  # Registered Face Images
```
