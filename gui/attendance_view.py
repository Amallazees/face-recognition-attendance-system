import threading
import cv2
from PIL import Image, ImageTk
import customtkinter as ctk
from gui.theme import (
    COLOR_BG, COLOR_CARD, COLOR_ACCENT, COLOR_SUCCESS,
    COLOR_DANGER, COLOR_WARNING, COLOR_TEXT, COLOR_SUBTEXT
)

class AttendanceScannerWindow(ctk.CTkToplevel):
    def __init__(self, parent, storage_manager, face_engine, sheets_manager):
        super().__init__(parent)
        self.storage_manager = storage_manager
        self.face_engine = face_engine
        self.sheets_manager = sheets_manager

        self.title("Live Face Attendance Scanner")
        self.geometry("900x650")
        self.configure(fg_color=COLOR_BG)

        self.cap = None
        self.is_running = False
        self.last_scanned_id = None
        self.cooldown_ticks = 0

        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self._build_ui()
        self._start_scanner()

    def _build_ui(self):
        # Header Banner
        header = ctk.CTkFrame(self, fg_color=COLOR_CARD, corner_radius=0, height=60)
        header.pack(fill="x", side="top")

        ctk.CTkLabel(
            header, text="📷 Live Attendance Scanner",
            font=("Segoe UI", 16, "bold"), text_color=COLOR_TEXT
        ).pack(side="left", padx=20, pady=15)

        self.lbl_sheets_status = ctk.CTkLabel(
            header, text="Google Sheets: Checking...",
            font=("Segoe UI", 11, "bold"), text_color=COLOR_WARNING
        )
        self.lbl_sheets_status.pack(side="right", padx=20)

        # Main Body
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=20, pady=15)

        # Video Frame Canvas
        self.cam_label = ctk.CTkLabel(body, text="Initializing Camera...", fg_color="#000000", corner_radius=12)
        self.cam_label.pack(fill="both", expand=True, pady=(0, 15))

        # Bottom Feedback Card
        self.status_card = ctk.CTkFrame(body, fg_color=COLOR_CARD, corner_radius=10, height=75)
        self.status_card.pack(fill="x")
        self.status_card.pack_propagate(False)

        self.lbl_status_main = ctk.CTkLabel(
            self.status_card, text="🔍 Look directly into the camera to mark attendance...",
            font=("Segoe UI", 13, "bold"), text_color=COLOR_TEXT
        )
        self.lbl_status_main.pack(anchor="w", padx=20, pady=(12, 2))

        self.lbl_status_sub = ctk.CTkLabel(
            self.status_card, text="System is scanning for registered student/staff faces.",
            font=("Segoe UI", 11), text_color=COLOR_SUBTEXT
        )
        self.lbl_status_sub.pack(anchor="w", padx=20)

        # Check Sheets Connection in background thread
        threading.Thread(target=self._check_sheets_connection, daemon=True).start()

    def _check_sheets_connection(self):
        connected, msg = self.sheets_manager.connect()
        if connected:
            self.lbl_sheets_status.configure(text="🌐 Google Sheets: Connected", text_color=COLOR_SUCCESS)
        else:
            self.lbl_sheets_status.configure(text="📁 Mode: Local CSV (Offline)", text_color=COLOR_SUBTEXT)

    def _start_scanner(self):
        self.cap = cv2.VideoCapture(0)
        self.is_running = True
        self._update_feed()

    def _stop_scanner(self):
        self.is_running = False
        if self.cap:
            self.cap.release()
            self.cap = None

    def _update_feed(self):
        if not self.is_running or self.cap is None:
            return

        ret, frame = self.cap.read()
        if ret:
            frame = cv2.flip(frame, 1)
            display_frame = frame.copy()
            faces = self.face_engine.detect_faces(frame)

            if len(faces) == 0:
                self.cooldown_ticks = max(0, self.cooldown_ticks - 1)
            else:
                for (x, y, w, h) in faces:
                    face_crop = frame[y:y+h, x:x+w]
                    student, confidence = self.face_engine.recognize_face(face_crop)

                    if student:
                        name = student.get("name", "Unknown")
                        adm = student.get("admission_no", "")
                        sid = student.get("id")

                        # Draw GREEN bounding box & text
                        cv2.rectangle(display_frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                        label = f"{name} ({confidence:.0f}%)"
                        cv2.putText(display_frame, label, (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

                        # Process attendance if cooldown passed or different student
                        if sid != self.last_scanned_id or self.cooldown_ticks <= 0:
                            self.last_scanned_id = sid
                            self.cooldown_ticks = 40 # ~2-3 seconds cooldown
                            self._trigger_attendance_marking(student)
                    else:
                        # Draw RED bounding box for unrecognized face
                        cv2.rectangle(display_frame, (x, y), (x+w, y+h), (0, 0, 255), 2)
                        cv2.putText(display_frame, "Unknown Face", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

            # Render to CustomTkinter widget
            img_rgb = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
            img_pil = Image.fromarray(img_rgb)
            img_ctk = ctk.CTkImage(light_image=img_pil, dark_image=img_pil, size=(720, 480))

            self.cam_label.configure(image=img_ctk, text="")
            self.cam_label.image = img_ctk

        self.after(30, self._update_feed)

    def _trigger_attendance_marking(self, student):
        # 1. Log locally
        success, msg, record = self.storage_manager.log_local_attendance(student)

        if success:
            self.lbl_status_main.configure(
                text=f"✅ Attendance Marked: {record.get('Name')} (Adm: {record.get('Admission No')})",
                text_color=COLOR_SUCCESS
            )
            self.lbl_status_sub.configure(
                text=f"Logged at {record.get('Time')} | Dept: {record.get('Department')}",
                text_color=COLOR_TEXT
            )

            # 2. Sync to Google Sheets in background thread
            threading.Thread(target=self._sync_to_google_sheet, args=(record,), daemon=True).start()
        else:
            self.lbl_status_main.configure(text=f"ℹ️ {msg}", text_color=COLOR_WARNING)
            self.lbl_status_sub.configure(text="Duplicate entry prevented for today.", text_color=COLOR_SUBTEXT)

    def _sync_to_google_sheet(self, record):
        sheet_success, sheet_msg = self.sheets_manager.log_attendance(record)
        if sheet_success:
            self.lbl_sheets_status.configure(text="🌐 Google Sheets: Synced!", text_color=COLOR_SUCCESS)
        else:
            self.lbl_sheets_status.configure(text="📁 Saved to Local CSV", text_color=COLOR_SUBTEXT)

    def _on_close(self):
        self._stop_scanner()
        self.destroy()
