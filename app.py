import sys
import os

# Add project root directory to python path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from gui.theme import setup_theme
from core.storage_manager import StorageManager
from core.face_engine import FaceEngine
from core.sheets_manager import SheetsManager
from gui.main_window import MainWindow

def main():
    # Setup CustomTkinter Theme
    setup_theme()

    # Initialize Core Subsystems
    storage_manager = StorageManager()
    face_engine = FaceEngine(storage_manager)
    sheets_manager = SheetsManager(storage_manager)

    # Launch Application GUI Window
    app = MainWindow(storage_manager, face_engine, sheets_manager)
    app.mainloop()

if __name__ == "__main__":
    main()
