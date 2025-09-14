#Libraries
import os

# ---- Paths ----
PKG_DIR    = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR   = os.path.dirname(PKG_DIR)
ASSETS_DIR = os.path.join(ROOT_DIR, "assets")
icon_path = os.path.join(ASSETS_DIR, "Logo_icon.png")
PDF_PATH   = os.path.join(ASSETS_DIR, "Control-All File.pdf")
LOGO_PATH  = os.path.join(ASSETS_DIR, "Logo.png")

VIDEOS_DIR = os.path.join(ASSETS_DIR, "videos")
AUDIOS_DIR = os.path.join(ASSETS_DIR, "audios")
MAPS_DIR   = os.path.join(ASSETS_DIR, "maps")

ALTERED_DIR = os.path.join(ASSETS_DIR, "AlteredItems")
OOP_DIR     = os.path.join(ASSETS_DIR, "OOP")

AHTI_IMAGE  = os.path.join(ASSETS_DIR, "Ahti.png")
AHTI_SONG   = os.path.join(ASSETS_DIR, "Sankarin Tango.mp3")
AHTI_CHANNEL_ID = 5

KEYSOUND_FILE = os.path.join(ASSETS_DIR, "keysound.mp3")

# ---- Runtime ----
FULLSCREEN = True
FPS        = 60

# Threshold Automatic 
THRESHOLD_MIN_DELAY = 120.0  
THRESHOLD_MAX_DELAY = 200.0
# ---- Theme (phosphor green) ----
BG     = (5, 16, 5)
FG     = (160, 255, 160)
MUTED  = (110, 200, 110)
ACCENT = (200, 255, 200)
BORDER = (20, 60, 20)

TITLE_TEXT = "FEDERAL BUREAU OF CONTROL"

# ---- Splash / Blink ----
BLINK_TIMES = 2
ON_MS, OFF_MS = 220, 160
SPLASH_DURATION = 4.0

# ---- Lock / Challenge ----
LOCK_ENABLED   = True
LOCK_CODE      = "1968"
LOCK_PASS2     = "BLACK ROCK"
LOCK_HINT      = "Hint: Northmoore facility, late 1960s."
LOCK_ATTEMPTS  = 3

# --- FBC Sectors (for random) ---
FBC_SECTORS = [
    "CENTRAL EXECUTIVE",
    "EXECUTIVE AFFAIRS",
    "RESEARCH / PARAPSYCHOLOGY",
    "DIMENSIONAL RESEARCH",
    "MAINTENANCE / NSC POWER PLANT",
    "ENERGY CONVERTERS",
    "VENTILATION",
    "CONTAINMENT",
    "PANOPTICON",
    "BLACK ROCK QUARRY",
    "LOGISTICS",
    "MAIL ROOM",
    "DEAD LETTERS",
    "RITUAL DIVISION",
    "LUCK & PROBABILITY LAB",
    "SYNCHRONICITY LAB",
    "COMMUNICATIONS DEPT.",
    "MEDICAL WING",
    "SECURITY",
    "FURNACE CHAMBER",
    "DATA ENTRY AND FILING",
    "PRIME CANDIDATE PROGRAM",
    "ASH TRAY MAZE",
]

# Quarry defaults
QUARRY_ROWS = 8       # A..H
QUARRY_COLS = 12      # 1..12
QUARRY_COOLDOWN = 15.0
