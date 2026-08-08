import os
import sys
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import time
from datetime import datetime
import customtkinter as ctk
from gui.theme import (
    COLOR_BG, COLOR_CARD, COLOR_CARD_HOVER, COLOR_ACCENT, COLOR_ACCENT_HOVER,
    COLOR_SUCCESS, COLOR_WARNING, COLOR_TEXT, COLOR_SUBTEXT
)
from gui.attendance_view import AttendanceScannerWindow
from gui.office_admin_view import PasswordDialog, OfficeAdminWindow
from gui.password_reset_view import PasswordResetWindow

class MainWindow(ctk.CTk):
    def __init__(self, storage_manager, face_engine, sheets_manager):
        super().__init__()
        self.storage_manager = storage_manager
        self.face_engine = face_engine
        self.sheets_manager = sheets_manager

        self.title("FACE RECOGNITION ATTENDANCE SYSTEM")
        self.geometry("1000x680")
        self.minsize(900, 600)
        self.configure(fg_color=COLOR_BG)

        self._build_ui()
        self._update_clock()

    def _build_ui(self):
        # Header Bar
        header = ctk.CTkFrame(self, fg_color=COLOR_CARD, corner_radius=0, height=90)
        header.pack(fill="x", side="top")

        # Header Title
        title_box = ctk.CTkFrame(header, fg_color="transparent")
        title_box.pack(side="left", padx=25, pady=12)

        ctk.CTkLabel(
            title_box, text="🎓 FACE RECOGNITION ATTENDANCE SYSTEM",
            font=("Segoe UI Black", 24, "bold"), text_color="#FFFFFF"
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_box, text="Smart AI Powered Attendance System",
            font=("Segoe UI", 12, "bold"), text_color=COLOR_SUBTEXT
        ).pack(anchor="w")

        # Header Right: Live Clock & Status
        self.lbl_clock = ctk.CTkLabel(
            header, text="", font=("Segoe UI", 13, "bold"), text_color=COLOR_ACCENT
        )
        self.lbl_clock.pack(side="right", padx=25)

        # Main Body Grid Container
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=30, pady=30)

        ctk.CTkLabel(
            body, text="Select an Option Below:",
            font=("Segoe UI", 15, "bold"), text_color=COLOR_TEXT
        ).pack(anchor="w", pady=(0, 20))

        # Cards Container Grid (3 Switches)
        grid_frame = ctk.CTkFrame(body, fg_color="transparent")
        grid_frame.pack(fill="both", expand=True)
        grid_frame.grid_columnconfigure((0, 1, 2), weight=1, uniform="card_group")

        # -------------------------------------------------------------
        # SWITCH 1: MARK ATTENDANCE
        # -------------------------------------------------------------
        card1 = ctk.CTkFrame(grid_frame, fg_color=COLOR_CARD, corner_radius=14)
        card1.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        ctk.CTkLabel(card1, text="📷", font=("Segoe UI", 48)).pack(pady=(25, 10))
        ctk.CTkLabel(card1, text="1. Mark Attendance", font=("Segoe UI", 16, "bold"), text_color=COLOR_TEXT).pack(pady=(0, 5))
        ctk.CTkLabel(
            card1,
            text="Open live camera scan, detect face & log attendance to Google Sheet.",
            font=("Segoe UI", 11), text_color=COLOR_SUBTEXT, wraplength=220, justify="center"
        ).pack(pady=(0, 25), padx=15)

        btn1 = ctk.CTkButton(
            card1, text="Launch Scanner 📷", font=("Segoe UI", 13, "bold"),
            fg_color=COLOR_ACCENT, hover_color=COLOR_ACCENT_HOVER, height=44,
            command=self._on_click_mark_attendance
        )
        btn1.pack(fill="x", padx=20, pady=(0, 25), side="bottom")

        # -------------------------------------------------------------
        # SWITCH 2: OFFICE USE ONLY
        # -------------------------------------------------------------
        card2 = ctk.CTkFrame(grid_frame, fg_color=COLOR_CARD, corner_radius=14)
        card2.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        ctk.CTkLabel(card2, text="🔒", font=("Segoe UI", 48)).pack(pady=(25, 10))
        ctk.CTkLabel(card2, text="2. Office Use Only", font=("Segoe UI", 16, "bold"), text_color=COLOR_TEXT).pack(pady=(0, 5))
        ctk.CTkLabel(
            card2,
            text="Password protected.\n1. Upload Students (Scan photo & save)\n2. Edit Student records",
            font=("Segoe UI", 11), text_color=COLOR_SUBTEXT, wraplength=220, justify="center"
        ).pack(pady=(0, 25), padx=15)

        btn2 = ctk.CTkButton(
            card2, text="Admin Access 🔒", font=("Segoe UI", 13, "bold"),
            fg_color="#D97706", hover_color="#B45309", height=44,
            command=self._on_click_office_use
        )
        btn2.pack(fill="x", padx=20, pady=(0, 25), side="bottom")

        # -------------------------------------------------------------
        # SWITCH 3: RESET PASSWORD
        # -------------------------------------------------------------
        card3 = ctk.CTkFrame(grid_frame, fg_color=COLOR_CARD, corner_radius=14)
        card3.grid(row=0, column=3, padx=10, pady=10, sticky="nsew")

        ctk.CTkLabel(card3, text="🔑", font=("Segoe UI", 48)).pack(pady=(25, 10))
        ctk.CTkLabel(card3, text="3. Reset Password", font=("Segoe UI", 16, "bold"), text_color=COLOR_TEXT).pack(pady=(0, 5))
        ctk.CTkLabel(
            card3,
            text="Update system admin password.\nRequires Current Password, New Password & Confirmation.",
            font=("Segoe UI", 11), text_color=COLOR_SUBTEXT, wraplength=220, justify="center"
        ).pack(pady=(0, 25), padx=15)

        btn3 = ctk.CTkButton(
            card3, text="Reset Password 🔑", font=("Segoe UI", 13, "bold"),
            fg_color=COLOR_CARD_HOVER, hover_color="#475569", height=44,
            command=self._on_click_reset_password
        )
        btn3.pack(fill="x", padx=20, pady=(0, 25), side="bottom")

        # Bottom Info Bar
        footer = ctk.CTkFrame(self, fg_color=COLOR_CARD, corner_radius=0, height=45)
        footer.pack(fill="x", side="bottom")

        self.lbl_stats = ctk.CTkLabel(
            footer, text=self._get_stats_text(), font=("Segoe UI", 11), text_color=COLOR_SUBTEXT
        )
        self.lbl_stats.pack(side="left", padx=25, pady=10)

        btn_settings = ctk.CTkButton(
            footer, text="⚙️ Google Sheet Settings", font=("Segoe UI", 11),
            fg_color="transparent", hover_color=COLOR_CARD_HOVER, width=160, height=30,
            command=self._open_settings_modal
        )
        btn_settings.pack(side="right", padx=20, pady=7)


    def _get_stats_text(self) -> str:
        count = len(self.storage_manager.get_students())
        return f"Registered Students/Staff: {count} | Storage: Local JSON + CSV"

    def _update_clock(self):
        now_str = datetime.now().strftime("%A, %b %d %Y  |  %I:%M:%S %p")
        self.lbl_clock.configure(text=now_str)
        self.after(1000, self._update_clock)

    # -------------------------------------------------------------
    # ACTION HANDLERS
    # -------------------------------------------------------------
    def _on_click_mark_attendance(self):
        AttendanceScannerWindow(self, self.storage_manager, self.face_engine, self.sheets_manager)

    def _on_click_office_use(self):
        def _open_admin():
            win = OfficeAdminWindow(self, self.storage_manager, self.face_engine)
            def _on_win_destroy(e):
                if e.widget == win and hasattr(self, 'lbl_stats') and self.lbl_stats.winfo_exists():
                    self.lbl_stats.configure(text=self._get_stats_text())
            win.bind("<Destroy>", _on_win_destroy)

        PasswordDialog(self, self.storage_manager, _open_admin)

    def _on_click_reset_password(self):
        PasswordResetWindow(self, self.storage_manager)

    def _open_settings_modal(self):
        modal = ctk.CTkToplevel(self)
        modal.title("Google Sheets Configuration")
        modal.geometry("450x420")
        modal.configure(fg_color=COLOR_CARD)
        modal.transient(self)
        modal.grab_set()

        container = ctk.CTkFrame(modal, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=25, pady=25)

        ctk.CTkLabel(container, text="⚙️ Google Sheets Settings", font=("Segoe UI", 16, "bold"), text_color=COLOR_TEXT).pack(anchor="w", pady=(0, 5))
        ctk.CTkLabel(container, text="Configure Sheet ID or Apps Script Webhook URL.", font=("Segoe UI", 11), text_color=COLOR_SUBTEXT).pack(anchor="w", pady=(0, 15))

        cfg = self.storage_manager.get_config()

        ctk.CTkLabel(container, text="Google Sheet ID", font=("Segoe UI", 11, "bold")).pack(anchor="w")
        e_sheet_id = ctk.CTkEntry(container, height=36)
        e_sheet_id.insert(0, cfg.get("google_sheet_id", ""))
        e_sheet_id.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(container, text="Google Apps Script URL (Optional)", font=("Segoe UI", 11, "bold")).pack(anchor="w")
        e_script_url = ctk.CTkEntry(container, height=36)
        e_script_url.insert(0, cfg.get("google_script_url", ""))
        e_script_url.pack(fill="x", pady=(0, 15))

        lbl_status = ctk.CTkLabel(container, text="", font=("Segoe UI", 11), wraplength=380)
        lbl_status.pack(pady=(0, 10))

        btn_row = ctk.CTkFrame(container, fg_color="transparent")
        btn_row.pack(fill="x")

        def _test_conn():
            cfg["google_sheet_id"] = e_sheet_id.get().strip()
            cfg["google_script_url"] = e_script_url.get().strip()
            self.storage_manager.save_config(cfg)
            lbl_status.configure(text="⏳ Testing connection...", text_color=COLOR_TEXT)
            success, msg = self.sheets_manager.test_connection()
            color = COLOR_SUCCESS if success else COLOR_WARNING
            lbl_status.configure(text=msg, text_color=color)

        def _save_cfg():
            cfg["google_sheet_id"] = e_sheet_id.get().strip()
            cfg["google_script_url"] = e_script_url.get().strip()
            self.storage_manager.save_config(cfg)
            lbl_status.configure(text="✅ Configuration saved!", text_color=COLOR_SUCCESS)
            self.after(1200, modal.destroy)

        ctk.CTkButton(btn_row, text="🧪 Test Connection", fg_color=COLOR_CARD_HOVER, height=40, font=("Segoe UI", 12, "bold"), command=_test_conn).pack(side="left", fill="x", expand=True, padx=(0, 5))
        ctk.CTkButton(btn_row, text="💾 Save Settings", fg_color=COLOR_ACCENT, height=40, font=("Segoe UI", 12, "bold"), command=_save_cfg).pack(side="right", fill="x", expand=True, padx=(5, 0))

if __name__ == "__main__":
    from app import main
    main()


