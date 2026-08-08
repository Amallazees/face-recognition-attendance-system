import customtkinter as ctk
from gui.theme import COLOR_CARD, COLOR_TEXT, COLOR_SUBTEXT, COLOR_ACCENT, COLOR_ACCENT_HOVER, COLOR_SUCCESS, COLOR_DANGER

class PasswordResetWindow(ctk.CTkToplevel):
    def __init__(self, parent, storage_manager):
        super().__init__(parent)
        self.storage_manager = storage_manager

        self.title("Reset Admin Password")
        self.geometry("450x480")
        self.resizable(False, False)
        self.configure(fg_color=COLOR_CARD)

        # Make modal
        self.transient(parent)
        self.grab_set()

        self._build_ui()

    def _build_ui(self):
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=30, pady=30)

        # Icon & Title
        title_label = ctk.CTkLabel(
            container,
            text="🔑 Reset Admin Password",
            font=("Segoe UI", 18, "bold"),
            text_color=COLOR_TEXT
        )
        title_label.pack(anchor="w", pady=(0, 5))

        subtitle_label = ctk.CTkLabel(
            container,
            text="Update your admin password for 'Office Use Only' access.",
            font=("Segoe UI", 11),
            text_color=COLOR_SUBTEXT
        )
        subtitle_label.pack(anchor="w", pady=(0, 20))

        # Current Password
        ctk.CTkLabel(container, text="Current Password", font=("Segoe UI", 12, "bold"), text_color=COLOR_TEXT).pack(anchor="w", pady=(5, 2))
        self.entry_current = ctk.CTkEntry(container, show="*", placeholder_text="Enter current password", height=40)
        self.entry_current.pack(fill="x", pady=(0, 15))

        # New Password
        ctk.CTkLabel(container, text="New Password", font=("Segoe UI", 12, "bold"), text_color=COLOR_TEXT).pack(anchor="w", pady=(5, 2))
        self.entry_new = ctk.CTkEntry(container, show="*", placeholder_text="Enter new password", height=40)
        self.entry_new.pack(fill="x", pady=(0, 15))

        # Confirm New Password
        ctk.CTkLabel(container, text="Confirm New Password", font=("Segoe UI", 12, "bold"), text_color=COLOR_TEXT).pack(anchor="w", pady=(5, 2))
        self.entry_confirm = ctk.CTkEntry(container, show="*", placeholder_text="Re-enter new password", height=40)
        self.entry_confirm.pack(fill="x", pady=(0, 15))

        # Status Message Label
        self.lbl_status = ctk.CTkLabel(container, text="", font=("Segoe UI", 11), text_color=COLOR_DANGER)
        self.lbl_status.pack(pady=(0, 10))

        # Save Button
        btn_save = ctk.CTkButton(
            container,
            text="Save New Password",
            height=42,
            font=("Segoe UI", 13, "bold"),
            fg_color=COLOR_ACCENT,
            hover_color=COLOR_ACCENT_HOVER,
            command=self._on_save
        )
        btn_save.pack(fill="x", pady=(5, 0))

    def _on_save(self):
        curr_pw = self.entry_current.get().strip()
        new_pw = self.entry_new.get().strip()
        confirm_pw = self.entry_confirm.get().strip()

        if not curr_pw or not new_pw or not confirm_pw:
            self.lbl_status.configure(text="⚠️ All fields are required.", text_color=COLOR_DANGER)
            return

        if new_pw != confirm_pw:
            self.lbl_status.configure(text="⚠️ New password and confirmation do not match.", text_color=COLOR_DANGER)
            return

        success, msg = self.storage_manager.update_password(curr_pw, new_pw)
        if success:
            self.lbl_status.configure(text=f"✅ {msg}", text_color=COLOR_SUCCESS)
            self.after(1500, self.destroy)
        else:
            self.lbl_status.configure(text=f"❌ {msg}", text_color=COLOR_DANGER)
