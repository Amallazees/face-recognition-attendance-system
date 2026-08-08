import os
import sys
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import cv2
from PIL import Image, ImageTk
import customtkinter as ctk
from gui.theme import (
    COLOR_BG, COLOR_CARD, COLOR_CARD_HOVER, COLOR_ACCENT, COLOR_ACCENT_HOVER,
    COLOR_SUCCESS, COLOR_DANGER, COLOR_WARNING, COLOR_TEXT, COLOR_SUBTEXT
)

class PasswordDialog(ctk.CTkToplevel):
    def __init__(self, parent, storage_manager, on_success_callback):
        super().__init__(parent)
        self.storage_manager = storage_manager
        self.on_success_callback = on_success_callback

        self.title("Office Admin Authentication")
        self.geometry("400x300")
        self.resizable(False, False)
        self.configure(fg_color=COLOR_CARD)

        self.transient(parent)
        self.grab_set()

        self._build_ui()

    def _build_ui(self):
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=30, pady=30)

        ctk.CTkLabel(container, text="🔒 Office Admin Access", font=("Segoe UI", 18, "bold"), text_color=COLOR_TEXT).pack(anchor="w", pady=(0, 5))
        ctk.CTkLabel(container, text="Please enter your admin password to continue.", font=("Segoe UI", 11), text_color=COLOR_SUBTEXT).pack(anchor="w", pady=(0, 20))

        self.entry_pw = ctk.CTkEntry(container, show="*", placeholder_text="Enter admin password", height=42)
        self.entry_pw.pack(fill="x", pady=(0, 10))
        self.entry_pw.bind("<Return>", lambda e: self._verify())

        self.lbl_error = ctk.CTkLabel(container, text="", font=("Segoe UI", 11), text_color=COLOR_DANGER)
        self.lbl_error.pack(pady=(0, 10))

        btn_login = ctk.CTkButton(
            container, text="Unlock Admin Panel", height=42,
            font=("Segoe UI", 13, "bold"), fg_color=COLOR_ACCENT,
            hover_color=COLOR_ACCENT_HOVER, command=self._verify
        )
        btn_login.pack(fill="x")

    def _verify(self):
        pw = self.entry_pw.get().strip()
        if self.storage_manager.verify_password(pw):
            self.destroy()
            self.on_success_callback()
        else:
            self.lbl_error.configure(text="❌ Incorrect password.")


class OfficeAdminWindow(ctk.CTkToplevel):
    def __init__(self, parent, storage_manager, face_engine):
        super().__init__(parent)
        self.storage_manager = storage_manager
        self.face_engine = face_engine

        self.title("Office Use Only - Admin Center")
        self.geometry("950x680")
        self.configure(fg_color=COLOR_BG)

        self.cap = None
        self.is_camera_running = False
        self.captured_frame = None
        self.captured_face_crop = None

        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self._build_ui()

    def _build_ui(self):
        # Header / Navigation Bar
        header_frame = ctk.CTkFrame(self, fg_color=COLOR_CARD, corner_radius=0, height=60)
        header_frame.pack(fill="x", side="top")

        ctk.CTkLabel(
            header_frame, text="🔒 Office Admin Dashboard",
            font=("Segoe UI", 16, "bold"), text_color=COLOR_TEXT
        ).pack(side="left", padx=20, pady=15)

        # Tab Segmented Switch (1. Upload Student, 2. Edit Student, 3. View Attendance Details)
        self.tab_switch = ctk.CTkSegmentedButton(
            header_frame,
            values=["1. Upload Students", "2. Edit Student", "3. View Attendance Details"],
            command=self._on_tab_change,
            selected_color=COLOR_ACCENT,
            font=("Segoe UI", 12, "bold"),
            height=36
        )
        self.tab_switch.set("1. Upload Students")
        self.tab_switch.pack(side="right", padx=20, pady=12)

        # Main Content Body Frame
        self.body_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.body_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Build Sub Views
        self._build_upload_student_view()
        self._build_edit_student_view()
        self._build_attendance_details_view()

        # Show initial tab
        self._show_upload_view()

    def _on_tab_change(self, value):
        if value == "1. Upload Students":
            self._show_upload_view()
        elif value == "2. Edit Student":
            self._show_edit_view()
        else:
            self._show_attendance_details_view()

    def _show_upload_view(self):
        self.edit_container.pack_forget()
        self.attendance_container.pack_forget()
        self.upload_container.pack(fill="both", expand=True)
        self._start_camera()

    def _show_edit_view(self):
        self._stop_camera()
        self.upload_container.pack_forget()
        self.attendance_container.pack_forget()
        self.edit_container.pack(fill="both", expand=True)
        self._refresh_student_list()

    # ==========================================
    # SUB-SWITCH 1: UPLOAD STUDENTS
    # ==========================================
    def _build_upload_student_view(self):
        self.upload_container = ctk.CTkFrame(self.body_frame, fg_color="transparent")

        # Left Column: Camera / Photo Capture Card
        left_card = ctk.CTkFrame(self.upload_container, fg_color=COLOR_CARD, corner_radius=12)
        left_card.pack(side="left", fill="both", expand=True, padx=(0, 10))

        ctk.CTkLabel(left_card, text="📸 Scan Student Photo", font=("Segoe UI", 14, "bold"), text_color=COLOR_TEXT).pack(anchor="w", padx=20, pady=(15, 5))
        ctk.CTkLabel(left_card, text="Position face inside camera frame & click capture.", font=("Segoe UI", 11), text_color=COLOR_SUBTEXT).pack(anchor="w", padx=20, pady=(0, 10))

        # Video Canvas Container
        self.cam_label = ctk.CTkLabel(left_card, text="Camera Loading...", fg_color="#000000", corner_radius=8)
        self.cam_label.pack(fill="both", expand=True, padx=20, pady=10)

        btn_row = ctk.CTkFrame(left_card, fg_color="transparent")
        btn_row.pack(fill="x", padx=20, pady=(5, 15))

        btn_cap = ctk.CTkButton(
            btn_row, text="📷 Capture Photo", font=("Segoe UI", 12, "bold"),
            fg_color=COLOR_ACCENT, hover_color=COLOR_ACCENT_HOVER, height=38,
            command=self._capture_photo
        )
        btn_cap.pack(side="left", fill="x", expand=True, padx=(0, 5))

        btn_retake = ctk.CTkButton(
            btn_row, text="🔄 Retake", font=("Segoe UI", 12, "bold"),
            fg_color=COLOR_CARD_HOVER, height=38,
            command=self._retake_photo
        )
        btn_retake.pack(side="right", padx=(5, 0))

        # Right Column: Registration Form Card
        right_card = ctk.CTkFrame(self.upload_container, fg_color=COLOR_CARD, corner_radius=12, width=380)
        right_card.pack(side="right", fill="both", padx=(10, 0))
        right_card.pack_propagate(False)

        ctk.CTkLabel(right_card, text="📝 Student Information", font=("Segoe UI", 14, "bold"), text_color=COLOR_TEXT).pack(anchor="w", padx=20, pady=(15, 15))

        # Form Fields
        ctk.CTkLabel(right_card, text="Full Name *", font=("Segoe UI", 11, "bold"), text_color=COLOR_TEXT).pack(anchor="w", padx=20, pady=(5, 2))
        self.entry_name = ctk.CTkEntry(right_card, placeholder_text="e.g. Rahul Sharma", height=38)
        self.entry_name.pack(fill="x", padx=20, pady=(0, 10))

        ctk.CTkLabel(right_card, text="Admission No *", font=("Segoe UI", 11, "bold"), text_color=COLOR_TEXT).pack(anchor="w", padx=20, pady=(5, 2))
        self.entry_adm = ctk.CTkEntry(right_card, placeholder_text="e.g. ADM202601", height=38)
        self.entry_adm.pack(fill="x", padx=20, pady=(0, 10))

        ctk.CTkLabel(right_card, text="Roll No *", font=("Segoe UI", 11, "bold"), text_color=COLOR_TEXT).pack(anchor="w", padx=20, pady=(5, 2))
        self.entry_roll = ctk.CTkEntry(right_card, placeholder_text="e.g. 101", height=38)
        self.entry_roll.pack(fill="x", padx=20, pady=(0, 10))

        ctk.CTkLabel(right_card, text="Department / Class", font=("Segoe UI", 11, "bold"), text_color=COLOR_TEXT).pack(anchor="w", padx=20, pady=(5, 2))
        self.entry_dept = ctk.CTkEntry(right_card, placeholder_text="e.g. Computer Science", height=38)
        self.entry_dept.pack(fill="x", padx=20, pady=(0, 15))

        self.lbl_upload_status = ctk.CTkLabel(right_card, text="", font=("Segoe UI", 11), text_color=COLOR_DANGER)
        self.lbl_upload_status.pack(pady=(0, 10))

        # Save Button
        btn_save = ctk.CTkButton(
            right_card, text="💾 Save Student", font=("Segoe UI", 13, "bold"),
            fg_color=COLOR_SUCCESS, hover_color="#059669", height=44,
            command=self._save_student
        )
        btn_save.pack(fill="x", padx=20, pady=(5, 20))

    def _start_camera(self):
        if not self.is_camera_running:
            self.cap = cv2.VideoCapture(0)
            self.is_camera_running = True
            self._update_camera_feed()

    def _stop_camera(self):
        self.is_camera_running = False
        if self.cap:
            self.cap.release()
            self.cap = None

    def _update_camera_feed(self):
        if not self.is_camera_running or self.cap is None:
            return

        ret, frame = self.cap.read()
        if ret:
            frame = cv2.flip(frame, 1) # mirror view
            self.current_frame = frame.copy()

            # Detect face for visual overlay box
            faces = self.face_engine.detect_faces(frame)
            display_frame = frame.copy()
            for (x, y, w, h) in faces:
                cv2.rectangle(display_frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                cv2.putText(display_frame, "Face Detected", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

            # Convert OpenCV frame to PIL Image for CustomTkinter
            img_rgb = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
            img_pil = Image.fromarray(img_rgb)
            img_ctk = ctk.CTkImage(light_image=img_pil, dark_image=img_pil, size=(480, 360))

            self.cam_label.configure(image=img_ctk, text="")
            self.cam_label.image = img_ctk

        self.after(30, self._update_camera_feed)

    def _capture_photo(self):
        if hasattr(self, 'current_frame') and self.current_frame is not None:
            frame = self.current_frame.copy()
            faces = self.face_engine.detect_faces(frame)

            if len(faces) == 0:
                self.lbl_upload_status.configure(text="⚠️ No face detected in frame. Adjust position.", text_color=COLOR_WARNING)
                return

            # Take primary detected face
            (x, y, w, h) = faces[0]
            # Add small padding around face crop
            h_img, w_img, _ = frame.shape
            pad = 20
            x1 = max(0, x - pad)
            y1 = max(0, y - pad)
            x2 = min(w_img, x + w + pad)
            y2 = min(h_img, y + h + pad)

            self.captured_frame = frame
            self.captured_face_crop = frame[y1:y2, x1:x2]

            # Pause camera & show preview snapshot
            self.is_camera_running = False

            crop_rgb = cv2.cvtColor(self.captured_face_crop, cv2.COLOR_BGR2RGB)
            crop_pil = Image.fromarray(crop_rgb)
            crop_ctk = ctk.CTkImage(light_image=crop_pil, dark_image=crop_pil, size=(300, 300))

            self.cam_label.configure(image=crop_ctk, text="")
            self.cam_label.image = crop_ctk

            self.lbl_upload_status.configure(text="✅ Photo captured! Now fill student details.", text_color=COLOR_SUCCESS)

    def _retake_photo(self):
        self.captured_frame = None
        self.captured_face_crop = None
        self.lbl_upload_status.configure(text="", text_color=COLOR_TEXT)
        self._start_camera()

    def _save_student(self):
        name = self.entry_name.get().strip()
        adm = self.entry_adm.get().strip()
        roll = self.entry_roll.get().strip()
        dept = self.entry_dept.get().strip()

        if not name or not adm or not roll:
            self.lbl_upload_status.configure(text="⚠️ Name, Admission No & Roll No are required.", text_color=COLOR_DANGER)
            return

        if self.captured_face_crop is None:
            self.lbl_upload_status.configure(text="⚠️ Please capture student photo first.", text_color=COLOR_DANGER)
            return

        student_data = {
            "name": name,
            "admission_no": adm,
            "roll_no": roll,
            "department": dept
        }

        success, msg = self.storage_manager.save_student(student_data)
        if not success:
            self.lbl_upload_status.configure(text=f"❌ {msg}", text_color=COLOR_DANGER)
            return

        # Save face photo image to data/faces/{id}.jpg
        saved_student = self.storage_manager.get_student_by_admission_no(adm)
        if saved_student:
            student_id = saved_student["id"]
            faces_dir = os.path.join(self.storage_manager.DATA_DIR if hasattr(self.storage_manager, 'DATA_DIR') else os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data"), "faces")
            photo_path = os.path.join(faces_dir, f"{student_id}.jpg")
            cv2.imwrite(photo_path, self.captured_face_crop)

        # Reload Face Engine Recognizer Dataset
        self.face_engine.reload_faces()

        self.lbl_upload_status.configure(text=f"🎉 {name} registered successfully!", text_color=COLOR_SUCCESS)

        # Reset Form
        self.entry_name.delete(0, 'end')
        self.entry_adm.delete(0, 'end')
        self.entry_roll.delete(0, 'end')
        self.entry_dept.delete(0, 'end')
        self._retake_photo()

    # ==========================================
    # SUB-SWITCH 2: EDIT STUDENT
    # ==========================================
    def _build_edit_student_view(self):
        self.edit_container = ctk.CTkFrame(self.body_frame, fg_color="transparent")

        # Top Filter Card
        filter_card = ctk.CTkFrame(self.edit_container, fg_color=COLOR_CARD, corner_radius=10)
        filter_card.pack(fill="x", pady=(0, 15))

        self.search_entry = ctk.CTkEntry(
            filter_card, placeholder_text="🔍 Search student by Name, Admission No, Roll No, or Department...",
            height=40, font=("Segoe UI", 12)
        )
        self.search_entry.pack(side="left", fill="x", expand=True, padx=15, pady=12)
        self.search_entry.bind("<KeyRelease>", lambda e: self._refresh_student_list())

        # Scrollable Student List Container
        self.scroll_list = ctk.CTkScrollableFrame(self.edit_container, fg_color="transparent")
        self.scroll_list.pack(fill="both", expand=True)

    def _refresh_student_list(self):
        for widget in self.scroll_list.winfo_children():
            widget.destroy()

        query = self.search_entry.get().strip().lower()
        students = self.storage_manager.get_students()

        if query:
            students = [
                s for s in students
                if query in s.get("name", "").lower()
                or query in s.get("admission_no", "").lower()
                or query in s.get("roll_no", "").lower()
                or query in s.get("department", "").lower()
            ]

        if not students:
            ctk.CTkLabel(self.scroll_list, text="No registered students found.", font=("Segoe UI", 13), text_color=COLOR_SUBTEXT).pack(pady=40)
            return

        for student in students:
            row_card = ctk.CTkFrame(self.scroll_list, fg_color=COLOR_CARD, corner_radius=10, height=70)
            row_card.pack(fill="x", pady=5)
            row_card.pack_propagate(False)

            # Details
            info_text = f"👤 {student.get('name')}  |  Adm: {student.get('admission_no')}  |  Roll: {student.get('roll_no')}  |  Dept: {student.get('department', 'N/A')}"
            ctk.CTkLabel(row_card, text=info_text, font=("Segoe UI", 12, "bold"), text_color=COLOR_TEXT).pack(side="left", padx=20)

            # Actions: Edit and Delete
            btn_del = ctk.CTkButton(
                row_card, text="🗑️ Delete", width=80, height=34,
                fg_color=COLOR_DANGER, hover_color="#DC2626", font=("Segoe UI", 11, "bold"),
                command=lambda s=student: self._delete_student(s)
            )
            btn_del.pack(side="right", padx=(5, 15))

            btn_edit = ctk.CTkButton(
                row_card, text="✏️ Edit", width=80, height=34,
                fg_color=COLOR_ACCENT, hover_color=COLOR_ACCENT_HOVER, font=("Segoe UI", 11, "bold"),
                command=lambda s=student: self._open_edit_modal(s)
            )
            btn_edit.pack(side="right", padx=5)

    def _open_edit_modal(self, student):
        modal = ctk.CTkToplevel(self)
        modal.title(f"Edit Student - {student.get('name')}")
        modal.geometry("400x460")
        modal.configure(fg_color=COLOR_CARD)
        modal.transient(self)
        modal.grab_set()

        container = ctk.CTkFrame(modal, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=25, pady=25)

        ctk.CTkLabel(container, text="✏️ Edit Student Info", font=("Segoe UI", 16, "bold"), text_color=COLOR_TEXT).pack(anchor="w", pady=(0, 15))

        ctk.CTkLabel(container, text="Full Name", font=("Segoe UI", 11, "bold")).pack(anchor="w")
        e_name = ctk.CTkEntry(container, height=36)
        e_name.insert(0, student.get('name', ''))
        e_name.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(container, text="Admission No", font=("Segoe UI", 11, "bold")).pack(anchor="w")
        e_adm = ctk.CTkEntry(container, height=36)
        e_adm.insert(0, student.get('admission_no', ''))
        e_adm.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(container, text="Roll No", font=("Segoe UI", 11, "bold")).pack(anchor="w")
        e_roll = ctk.CTkEntry(container, height=36)
        e_roll.insert(0, student.get('roll_no', ''))
        e_roll.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(container, text="Department", font=("Segoe UI", 11, "bold")).pack(anchor="w")
        e_dept = ctk.CTkEntry(container, height=36)
        e_dept.insert(0, student.get('department', ''))
        e_dept.pack(fill="x", pady=(0, 15))

        lbl_modal_status = ctk.CTkLabel(container, text="", font=("Segoe UI", 11), text_color=COLOR_DANGER)
        lbl_modal_status.pack(pady=(0, 10))

        def _save_changes():
            student['name'] = e_name.get().strip()
            student['admission_no'] = e_adm.get().strip()
            student['roll_no'] = e_roll.get().strip()
            student['department'] = e_dept.get().strip()

            success, msg = self.storage_manager.save_student(student)
            if success:
                self.face_engine.reload_faces()
                self._refresh_student_list()
                modal.destroy()
            else:
                lbl_modal_status.configure(text=f"❌ {msg}")

        ctk.CTkButton(container, text="Save Updates", fg_color=COLOR_SUCCESS, height=40, font=("Segoe UI", 12, "bold"), command=_save_changes).pack(fill="x")

    def _delete_student(self, student):
        sid = student.get("id")
        name = student.get("name")
        success, msg = self.storage_manager.delete_student(sid)
        if success:
            self.face_engine.reload_faces()
            self._refresh_student_list()

    # ==========================================
    # SUB-SWITCH 3: VIEW ATTENDANCE DETAILS
    # ==========================================
    def _build_attendance_details_view(self):
        self.attendance_container = ctk.CTkFrame(self.body_frame, fg_color="transparent")

        # Top Control Bar (Search & Upper Right Corner Download PDF Button)
        ctrl_card = ctk.CTkFrame(self.attendance_container, fg_color=COLOR_CARD, corner_radius=10, height=65)
        ctrl_card.pack(fill="x", pady=(0, 15))
        ctrl_card.pack_propagate(False)

        # Left: Search Bar
        self.att_search_entry = ctk.CTkEntry(
            ctrl_card, placeholder_text="🔍 Search Name, Admission No, Roll No...",
            height=38, font=("Segoe UI", 12), width=320
        )
        self.att_search_entry.pack(side="left", padx=15, pady=13)
        self.att_search_entry.bind("<KeyRelease>", lambda e: self._refresh_attendance_table())

        # Right Upper Corner: "📄 Download as PDF" Button
        btn_export_pdf = ctk.CTkButton(
            ctrl_card, text="📄 Download as PDF", font=("Segoe UI", 12, "bold"),
            fg_color=COLOR_SUCCESS, hover_color="#059669", height=38, width=170,
            command=self._export_pdf_report
        )
        btn_export_pdf.pack(side="right", padx=15, pady=13)

        # Summary Text Label
        self.lbl_att_count = ctk.CTkLabel(ctrl_card, text="Total Records: 0", font=("Segoe UI", 11, "bold"), text_color=COLOR_SUBTEXT)
        self.lbl_att_count.pack(side="right", padx=15, pady=13)

        # Main Data Sheet Container
        table_card = ctk.CTkFrame(self.attendance_container, fg_color=COLOR_CARD, corner_radius=10)
        table_card.pack(fill="both", expand=True)

        # Data Sheet Header Row
        header_row = ctk.CTkFrame(table_card, fg_color=COLOR_CARD_HOVER, corner_radius=6, height=40)
        header_row.pack(fill="x", padx=10, pady=(10, 5))
        header_row.pack_propagate(False)

        cols = [("Date", 85), ("Time", 85), ("Adm No", 95), ("Name", 150), ("Roll No", 60), ("Department", 100), ("Status", 65), ("Actions", 100)]
        for col_name, col_w in cols:
            ctk.CTkLabel(header_row, text=col_name, font=("Segoe UI", 11, "bold"), text_color=COLOR_TEXT, width=col_w, anchor="w").pack(side="left", padx=4)

        # Scrollable Data List
        self.att_scroll_list = ctk.CTkScrollableFrame(table_card, fg_color="transparent")
        self.att_scroll_list.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    def _show_attendance_details_view(self):
        self._stop_camera()
        self.upload_container.pack_forget()
        self.edit_container.pack_forget()
        self.attendance_container.pack(fill="both", expand=True)
        self._refresh_attendance_table()

    def _refresh_attendance_table(self):
        for widget in self.att_scroll_list.winfo_children():
            widget.destroy()

        query = self.att_search_entry.get().strip()
        records = self.storage_manager.get_attendance_records(search_query=query)

        self.lbl_att_count.configure(text=f"Total Records: {len(records)}")

        if not records:
            ctk.CTkLabel(self.att_scroll_list, text="No attendance records found.", font=("Segoe UI", 13), text_color=COLOR_SUBTEXT).pack(pady=40)
            return

        for r in records:
            row_frame = ctk.CTkFrame(self.att_scroll_list, fg_color="transparent", height=38)
            row_frame.pack(fill="x", pady=2)
            row_frame.pack_propagate(False)

            ctk.CTkLabel(row_frame, text=r.get("Date", ""), font=("Segoe UI", 11), text_color=COLOR_TEXT, width=85, anchor="w").pack(side="left", padx=4)
            ctk.CTkLabel(row_frame, text=r.get("Time", ""), font=("Segoe UI", 10), text_color=COLOR_SUBTEXT, width=85, anchor="w").pack(side="left", padx=4)
            ctk.CTkLabel(row_frame, text=r.get("Admission No", ""), font=("Segoe UI", 11, "bold"), text_color=COLOR_ACCENT, width=95, anchor="w").pack(side="left", padx=4)
            ctk.CTkLabel(row_frame, text=r.get("Name", ""), font=("Segoe UI", 11, "bold"), text_color=COLOR_TEXT, width=150, anchor="w").pack(side="left", padx=4)
            ctk.CTkLabel(row_frame, text=r.get("Roll No", ""), font=("Segoe UI", 11), text_color=COLOR_TEXT, width=60, anchor="w").pack(side="left", padx=4)
            ctk.CTkLabel(row_frame, text=r.get("Department", ""), font=("Segoe UI", 11), text_color=COLOR_SUBTEXT, width=110, anchor="w").pack(side="left", padx=4)
            ctk.CTkLabel(row_frame, text=r.get("Status", "Present"), font=("Segoe UI", 11, "bold"), text_color=COLOR_SUCCESS, width=65, anchor="w").pack(side="left", padx=4)

            # Actions Frame (Edit & Delete Buttons)
            actions_frame = ctk.CTkFrame(row_frame, fg_color="transparent", width=100)
            actions_frame.pack(side="left", padx=4)

            btn_edit = ctk.CTkButton(
                actions_frame, text="✏️", width=34, height=28,
                fg_color=COLOR_ACCENT, hover_color=COLOR_ACCENT_HOVER, font=("Segoe UI", 11),
                command=lambda rec=r: self._open_edit_attendance_modal(rec)
            )
            btn_edit.pack(side="left", padx=2)

            btn_del = ctk.CTkButton(
                actions_frame, text="🗑️", width=34, height=28,
                fg_color=COLOR_DANGER, hover_color="#DC2626", font=("Segoe UI", 11),
                command=lambda rec=r: self._delete_attendance_record(rec)
            )
            btn_del.pack(side="left", padx=2)

    def _open_edit_attendance_modal(self, record):
        modal = ctk.CTkToplevel(self)
        modal.title(f"Edit Attendance - {record.get('Name')}")
        modal.geometry("420x520")
        modal.configure(fg_color=COLOR_CARD)
        modal.transient(self)
        modal.grab_set()

        container = ctk.CTkFrame(modal, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=25, pady=20)

        ctk.CTkLabel(container, text="✏️ Edit Attendance Record", font=("Segoe UI", 16, "bold"), text_color=COLOR_TEXT).pack(anchor="w", pady=(0, 10))

        ctk.CTkLabel(container, text="Full Name", font=("Segoe UI", 11, "bold")).pack(anchor="w")
        e_name = ctk.CTkEntry(container, height=34)
        e_name.insert(0, record.get('Name', ''))
        e_name.pack(fill="x", pady=(0, 8))

        ctk.CTkLabel(container, text="Admission No", font=("Segoe UI", 11, "bold")).pack(anchor="w")
        e_adm = ctk.CTkEntry(container, height=34)
        e_adm.insert(0, record.get('Admission No', ''))
        e_adm.pack(fill="x", pady=(0, 8))

        ctk.CTkLabel(container, text="Roll No", font=("Segoe UI", 11, "bold")).pack(anchor="w")
        e_roll = ctk.CTkEntry(container, height=34)
        e_roll.insert(0, record.get('Roll No', ''))
        e_roll.pack(fill="x", pady=(0, 8))

        ctk.CTkLabel(container, text="Department", font=("Segoe UI", 11, "bold")).pack(anchor="w")
        e_dept = ctk.CTkEntry(container, height=34)
        e_dept.insert(0, record.get('Department', ''))
        e_dept.pack(fill="x", pady=(0, 8))

        ctk.CTkLabel(container, text="Date (YYYY-MM-DD)", font=("Segoe UI", 11, "bold")).pack(anchor="w")
        e_date = ctk.CTkEntry(container, height=34)
        e_date.insert(0, record.get('Date', ''))
        e_date.pack(fill="x", pady=(0, 8))

        ctk.CTkLabel(container, text="Status", font=("Segoe UI", 11, "bold")).pack(anchor="w")
        e_status = ctk.CTkEntry(container, height=34)
        e_status.insert(0, record.get('Status', 'Present'))
        e_status.pack(fill="x", pady=(0, 12))

        lbl_status = ctk.CTkLabel(container, text="", font=("Segoe UI", 11), text_color=COLOR_DANGER)
        lbl_status.pack(pady=(0, 8))

        def _save():
            updated = {
                "Date": e_date.get().strip(),
                "Time": record.get("Time"),
                "Admission No": e_adm.get().strip(),
                "Name": e_name.get().strip(),
                "Roll No": e_roll.get().strip(),
                "Department": e_dept.get().strip(),
                "Status": e_status.get().strip()
            }
            success, msg = self.storage_manager.update_attendance_record(record, updated)
            if success:
                self._refresh_attendance_table()
                modal.destroy()
            else:
                lbl_status.configure(text=f"❌ {msg}")

        ctk.CTkButton(container, text="💾 Save Changes", fg_color=COLOR_SUCCESS, height=38, font=("Segoe UI", 12, "bold"), command=_save).pack(fill="x")

    def _delete_attendance_record(self, record):
        success, msg = self.storage_manager.delete_attendance_record(record)
        if success:
            self._refresh_attendance_table()

    def _export_pdf_report(self):
        from tkinter import filedialog, messagebox
        from datetime import datetime
        import os

        query = self.att_search_entry.get().strip()
        records = self.storage_manager.get_attendance_records(search_query=query)

        if not records:
            messagebox.showwarning("No Data", "There are no attendance records to export.")
            return

        default_filename = f"Attendance_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        file_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF Document", "*.pdf")],
            initialfile=default_filename,
            title="Save Attendance Report PDF"
        )

        if file_path:
            success, msg = self.storage_manager.export_attendance_pdf(records, file_path)
            if success:
                try:
                    os.startfile(file_path)
                except Exception:
                    pass
            else:
                messagebox.showerror("Export Failed", msg)

    def _on_close(self):
        self._stop_camera()
        self.destroy()

if __name__ == "__main__":
    from app import main
    main()

