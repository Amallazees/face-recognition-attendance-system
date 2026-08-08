import customtkinter as ctk

# Color Palette (Modern Dark Slate & Cyan/Blue Accent)
THEME_DARK = "dark"
THEME_COLOR = "blue"

COLOR_BG = "#0F172A"         # Slate 900
COLOR_CARD = "#1E293B"       # Slate 800
COLOR_CARD_HOVER = "#334155" # Slate 700
COLOR_ACCENT = "#2563EB"     # Royal Blue
COLOR_ACCENT_HOVER = "#1D4ED8"
COLOR_SUCCESS = "#10B981"    # Emerald
COLOR_DANGER = "#EF4444"     # Rose / Red
COLOR_WARNING = "#F59E0B"    # Amber
COLOR_TEXT = "#F8FAFC"       # Slate 50
COLOR_SUBTEXT = "#94A3B8"    # Slate 400

FONT_TITLE = ("Segoe UI", 22, "bold")
FONT_SUBTITLE = ("Segoe UI", 14, "bold")
FONT_BODY = ("Segoe UI", 12)
FONT_CAPTION = ("Segoe UI", 10)

def setup_theme():
    ctk.set_appearance_mode(THEME_DARK)
    ctk.set_default_color_theme(THEME_COLOR)
