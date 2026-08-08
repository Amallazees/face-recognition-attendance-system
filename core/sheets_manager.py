import os
import json
import requests
from datetime import datetime

class SheetsManager:
    def __init__(self, storage_manager):
        self.storage_manager = storage_manager
        self.client = None
        self.sheet = None

    def connect(self) -> tuple[bool, str]:
        """Attempts to connect to Google Sheets using gspread or Google Script URL."""
        config = self.storage_manager.get_config()
        sheet_id = config.get("google_sheet_id", "").strip()
        credentials_file = config.get("google_credentials_file", "credentials.json").strip()
        script_url = config.get("google_script_url", "").strip()

        # Try Google Script Webhook first if defined
        if script_url:
            try:
                # Test ping request to script URL
                resp = requests.get(script_url, timeout=5)
                if resp.status_code in [200, 302]:
                    return True, "Connected via Google Apps Script Webhook."
            except Exception as e:
                pass

        # Try gspread with Service Account JSON
        if sheet_id:
            try:
                import gspread
                from google.oauth2.service_account import Credentials

                scopes = [
                    "https://www.googleapis.com/auth/spreadsheets",
                    "https://www.googleapis.com/auth/drive"
                ]

                # Find credentials file in project root or custom path
                base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                creds_path = os.path.join(base_dir, credentials_file) if not os.path.isabs(credentials_file) else credentials_file

                if os.path.exists(creds_path):
                    creds = Credentials.from_service_account_file(creds_path, scopes=scopes)
                    self.client = gspread.authorize(creds)
                    self.sheet = self.client.open_by_key(sheet_id).sheet1
                else:
                    return False, f"Credentials file '{credentials_file}' not found."
            except Exception as e:
                return False, f"Google Sheets error: {str(e)}"

        return False, "Google Sheet ID or Credentials not configured."

    def test_connection(self) -> tuple[bool, str]:
        """Sends a test row or pings the configured Google Sheet / Webhook."""
        config = self.storage_manager.get_config()
        script_url = config.get("google_script_url", "").strip()
        sheet_id = config.get("google_sheet_id", "").strip()

        if script_url:
            try:
                test_payload = {
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "time": datetime.now().strftime("%I:%M:%S %p"),
                    "admission_no": "TEST001",
                    "name": "Test Connection",
                    "roll_no": "0",
                    "department": "System Check",
                    "status": "Test Sync"
                }
                resp = requests.post(script_url, json=test_payload, timeout=8)
                if resp.status_code in [200, 201]:
                    return True, "✅ Success! Google Apps Script Webhook is active and receiving data."
                else:
                    return False, f"⚠️ Webhook returned HTTP {resp.status_code}. Check deployment permissions."
            except Exception as e:
                return False, f"❌ Webhook connection failed: {str(e)}"

        if sheet_id:
            connected, msg = self.connect()
            if connected:
                return True, f"✅ Success! {msg}"
            else:
                return False, f"❌ Connection failed: {msg}"

        return False, "⚠️ Neither Google Script URL nor Service Account credentials file found."


    def log_attendance(self, record: dict) -> tuple[bool, str]:
        """Appends attendance record to Google Sheets."""
        config = self.storage_manager.get_config()
        script_url = config.get("google_script_url", "").strip()

        # Method A: Google Apps Script Webhook
        if script_url:
            try:
                payload = {
                    "date": record.get("Date"),
                    "time": record.get("Time"),
                    "admission_no": record.get("Admission No"),
                    "name": record.get("Name"),
                    "roll_no": record.get("Roll No"),
                    "department": record.get("Department"),
                    "status": record.get("Status")
                }
                resp = requests.post(script_url, json=payload, timeout=8)
                if resp.status_code in [200, 201]:
                    return True, "Synced with Google Sheet (Webhook)."
            except Exception as e:
                return False, f"Webhook Sync Failed: {str(e)}"

        # Method B: gspread API
        if self.sheet is None:
            connected, msg = self.connect()
            if not connected:
                return False, f"Not connected: {msg}"

        if self.sheet:
            try:
                row = [
                    record.get("Date"),
                    record.get("Time"),
                    record.get("Admission No"),
                    record.get("Name"),
                    record.get("Roll No"),
                    record.get("Department"),
                    record.get("Status")
                ]
                self.sheet.append_row(row)
                return True, "Synced to Google Sheet!"
            except Exception as e:
                # Retry connection once
                try:
                    self.connect()
                    if self.sheet:
                        self.sheet.append_row(row)
                        return True, "Synced to Google Sheet!"
                except Exception as ex:
                    return False, f"Sheet Append Error: {str(ex)}"

        return False, "Google Sheet connection not available."
