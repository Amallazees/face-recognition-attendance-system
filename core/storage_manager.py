import os
import json
import csv
import hashlib
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
FACES_DIR = os.path.join(DATA_DIR, "faces")
STUDENTS_FILE = os.path.join(DATA_DIR, "students.json")
CONFIG_FILE = os.path.join(DATA_DIR, "config.json")
ATTENDANCE_FILE = os.path.join(DATA_DIR, "attendance.csv")

DEFAULT_PASSWORD = "Amal@123"

def hash_password(password: str) -> str:
    """Hash password using SHA-256."""
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

class StorageManager:
    def __init__(self):
        self._ensure_directories()
        self._init_config()
        self._init_students()
        self._init_attendance()

    def _ensure_directories(self):
        os.makedirs(DATA_DIR, exist_ok=True)
        os.makedirs(FACES_DIR, exist_ok=True)

    def _init_config(self):
        if not os.path.exists(CONFIG_FILE):
            default_config = {
                "password_hash": hash_password(DEFAULT_PASSWORD),
                "google_sheet_id": "",
                "google_credentials_file": "credentials.json",
                "google_script_url": "",
                "created_at": datetime.now().isoformat()
            }
            self.save_config(default_config)

    def _init_students(self):
        if not os.path.exists(STUDENTS_FILE):
            with open(STUDENTS_FILE, "w", encoding="utf-8") as f:
                json.dump([], f, indent=4)

    def _init_attendance(self):
        if not os.path.exists(ATTENDANCE_FILE):
            with open(ATTENDANCE_FILE, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["Date", "Time", "Admission No", "Name", "Roll No", "Department", "Status"])

    def get_config(self) -> dict:
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def save_config(self, config: dict):
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4)

    def verify_password(self, input_password: str) -> bool:
        config = self.get_config()
        stored_hash = config.get("password_hash", "")
        return stored_hash == hash_password(input_password)

    def update_password(self, current_password: str, new_password: str) -> tuple[bool, str]:
        if not self.verify_password(current_password):
            return False, "Current password is incorrect."
        if not new_password or len(new_password) < 4:
            return False, "New password must be at least 4 characters long."

        config = self.get_config()
        config["password_hash"] = hash_password(new_password)
        self.save_config(config)
        return True, "Password updated successfully!"

    def get_students(self) -> list:
        try:
            with open(STUDENTS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def get_student_by_admission_no(self, admission_no: str) -> dict | None:
        students = self.get_students()
        for s in students:
            if s.get("admission_no", "").strip().lower() == admission_no.strip().lower():
                return s
        return None

    def get_student_by_id(self, student_id: str) -> dict | None:
        students = self.get_students()
        for s in students:
            if str(s.get("id")) == str(student_id):
                return s
        return None

    def save_student(self, student_data: dict) -> tuple[bool, str]:
        students = self.get_students()
        adm_no = student_data.get("admission_no", "").strip()
        
        if not adm_no:
            return False, "Admission number is required."

        # Check for existing duplicate admission_no if new student
        existing = self.get_student_by_admission_no(adm_no)
        if existing and existing.get("id") != student_data.get("id"):
            return False, f"Student with Admission No '{adm_no}' already exists."

        # Assign ID if new
        if "id" not in student_data or not student_data["id"]:
            student_data["id"] = f"STD_{int(datetime.now().timestamp() * 1000)}"

        student_data["updated_at"] = datetime.now().isoformat()
        if "created_at" not in student_data:
            student_data["created_at"] = datetime.now().isoformat()

        # Update or append
        updated = False
        for i, s in enumerate(students):
            if s.get("id") == student_data["id"]:
                students[i] = student_data
                updated = True
                break
        
        if not updated:
            students.append(student_data)

        with open(STUDENTS_FILE, "w", encoding="utf-8") as f:
            json.dump(students, f, indent=4)

        return True, "Student saved successfully."

    def delete_student(self, student_id: str) -> tuple[bool, str]:
        students = self.get_students()
        initial_len = len(students)
        students = [s for s in students if str(s.get("id")) != str(student_id)]

        if len(students) == initial_len:
            return False, "Student not found."

        with open(STUDENTS_FILE, "w", encoding="utf-8") as f:
            json.dump(students, f, indent=4)

        # Also remove face photo if exists
        photo_path = os.path.join(FACES_DIR, f"{student_id}.jpg")
        if os.path.exists(photo_path):
            try:
                os.remove(photo_path)
            except Exception:
                pass

        return True, "Student deleted successfully."

    def is_attendance_marked_today(self, admission_no: str) -> bool:
        today_str = datetime.now().strftime("%Y-%m-%d")
        if not os.path.exists(ATTENDANCE_FILE):
            return False

        try:
            with open(ATTENDANCE_FILE, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                header = next(reader, None)
                for row in reader:
                    if len(row) >= 3:
                        row_date = row[0]
                        row_adm = row[2]
                        if row_date == today_str and row_adm.strip().lower() == admission_no.strip().lower():
                            return True
        except Exception:
            pass

        return False

    def log_local_attendance(self, student_data: dict) -> tuple[bool, str, dict]:
        adm_no = student_data.get("admission_no", "")
        if self.is_attendance_marked_today(adm_no):
            return False, f"Attendance already marked today for {student_data.get('name', '')}.", {}

        now = datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        time_str = now.strftime("%I:%M:%S %p")

        record = {
            "Date": date_str,
            "Time": time_str,
            "Admission No": student_data.get("admission_no", "N/A"),
            "Name": student_data.get("name", "Unknown"),
            "Roll No": student_data.get("roll_no", "N/A"),
            "Department": student_data.get("department", "N/A"),
            "Status": "Present"
        }

        try:
            with open(ATTENDANCE_FILE, "a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([
                    record["Date"],
                    record["Time"],
                    record["Admission No"],
                    record["Name"],
                    record["Roll No"],
                    record["Department"],
                    record["Status"]
                ])
            return True, f"Attendance marked for {record['Name']}!", record
        except Exception as e:
            return False, f"Error logging attendance: {str(e)}", {}

    def get_attendance_records(self, date_filter: str = None, search_query: str = None) -> list[dict]:
        """Reads attendance CSV records with optional filtering."""
        records = []
        if not os.path.exists(ATTENDANCE_FILE):
            return records

        try:
            with open(ATTENDANCE_FILE, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                header = next(reader, None)
                for row in reader:
                    if len(row) >= 7:
                        r_date, r_time, r_adm, r_name, r_roll, r_dept, r_status = row[:7]
                        
                        # Filter by Date
                        if date_filter and date_filter != "All Dates" and r_date != date_filter:
                            continue

                        # Filter by Search Query
                        if search_query:
                            q = search_query.lower()
                            if not (q in r_name.lower() or q in r_adm.lower() or q in r_roll.lower() or q in r_dept.lower()):
                                continue

                        records.append({
                            "Date": r_date,
                            "Time": r_time,
                            "Admission No": r_adm,
                            "Name": r_name,
                            "Roll No": r_roll,
                            "Department": r_dept,
                            "Status": r_status
                        })
        except Exception:
            pass

        # Sort reverse chronological (newest first)
        records.reverse()
        return records

    def delete_attendance_record(self, target_record: dict) -> tuple[bool, str]:
        """Deletes a specific attendance record row from CSV."""
        if not os.path.exists(ATTENDANCE_FILE):
            return False, "Attendance record file not found."

        all_rows = []
        deleted = False

        try:
            with open(ATTENDANCE_FILE, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                header = next(reader, None)
                if header:
                    all_rows.append(header)
                
                for row in reader:
                    if len(row) >= 7:
                        if (row[0] == target_record.get("Date") and
                            row[1] == target_record.get("Time") and
                            row[2] == target_record.get("Admission No")):
                            deleted = True
                            continue
                    all_rows.append(row)

            if deleted:
                with open(ATTENDANCE_FILE, "w", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerows(all_rows)
                return True, "Attendance record deleted successfully."
            else:
                return False, "Record not found."
        except Exception as e:
            return False, f"Error deleting record: {str(e)}"

    def update_attendance_record(self, original_record: dict, updated_record: dict) -> tuple[bool, str]:
        """Updates a specific attendance record row in CSV."""
        if not os.path.exists(ATTENDANCE_FILE):
            return False, "Attendance record file not found."

        all_rows = []
        updated = False

        try:
            with open(ATTENDANCE_FILE, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                header = next(reader, None)
                if header:
                    all_rows.append(header)

                for row in reader:
                    if len(row) >= 7:
                        if (row[0] == original_record.get("Date") and
                            row[1] == original_record.get("Time") and
                            row[2] == original_record.get("Admission No")):
                            new_row = [
                                updated_record.get("Date", row[0]),
                                updated_record.get("Time", row[1]),
                                updated_record.get("Admission No", row[2]),
                                updated_record.get("Name", row[3]),
                                updated_record.get("Roll No", row[4]),
                                updated_record.get("Department", row[5]),
                                updated_record.get("Status", row[6])
                            ]
                            all_rows.append(new_row)
                            updated = True
                            continue
                    all_rows.append(row)

            if updated:
                with open(ATTENDANCE_FILE, "w", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerows(all_rows)
                return True, "Attendance record updated successfully."
            else:
                return False, "Record not found."
        except Exception as e:
            return False, f"Error updating record: {str(e)}"

    def export_attendance_pdf(self, records: list[dict], output_path: str) -> tuple[bool, str]:
        """Generates a styled PDF report for attendance records."""
        try:
            from reportlab.lib.pagesizes import letter, A4
            from reportlab.lib import colors
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

            doc = SimpleDocTemplate(
                output_path,
                pagesize=A4,
                rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30
            )

            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                'DocTitle',
                parent=styles['Heading1'],
                fontSize=18,
                textColor=colors.HexColor('#0F172A'),
                spaceAfter=6
            )
            sub_style = ParagraphStyle(
                'DocSubTitle',
                parent=styles['Normal'],
                fontSize=10,
                textColor=colors.HexColor('#64748B'),
                spaceAfter=15
            )

            elements = []
            
            # Title & Metadata Header
            elements.append(Paragraph("<b>ATTENDANCE REPORT</b>", title_style))
            gen_time = datetime.now().strftime("%Y-%m-%d %I:%M %p")
            elements.append(Paragraph(f"Generated on: {gen_time} &nbsp;|&nbsp; Total Records: {len(records)}", sub_style))

            # Table Header Data
            table_data = [
                ["Date", "Time", "Admission No", "Name", "Roll No", "Department", "Status"]
            ]

            cell_style = ParagraphStyle('Cell', fontSize=9, leading=11, textColor=colors.HexColor('#1E293B'))

            for r in records:
                table_data.append([
                    Paragraph(r.get("Date", ""), cell_style),
                    Paragraph(r.get("Time", ""), cell_style),
                    Paragraph(r.get("Admission No", ""), cell_style),
                    Paragraph(r.get("Name", ""), cell_style),
                    Paragraph(r.get("Roll No", ""), cell_style),
                    Paragraph(r.get("Department", ""), cell_style),
                    Paragraph(f"<b>{r.get('Status', '')}</b>", cell_style)
                ])

            # Column widths for A4 (total ~535pt)
            col_widths = [65, 75, 85, 120, 50, 80, 60]

            t = Table(table_data, colWidths=col_widths, repeatRows=1)
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E293B')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('TOPPADDING', (0, 0), (-1, 0), 8),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#F8FAFC'), colors.white]),
            ]))

            elements.append(t)
            doc.build(elements)
            return True, f"PDF exported successfully to:\n{output_path}"
        except Exception as e:
            return False, f"PDF Export Failed: {str(e)}"

