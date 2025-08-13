# config.py
# Flattrade API Configuration

# ===== API Credentials =====
API_KEY = "a2f996137c6941d1a548abe55908afb9"
API_SECRET = "2025.c5a03507a5a34b1e9bb831c0135c9b8e87ae869115d01229"
CLIENT_ID = "FT040233"

# ===== TOTP (Authenticator App Secret) =====
TOTP_SECRET = "5A5A34TP43CU74G6VHJ5IA6ILAA7442N"

# ===== Trading Settings =====
LOT_SIZE = 65
SYMBOL = "FINNIFTY"
EXCHANGE = "NFO"

# ===== Time Settings =====
START_TIME = "09:20"  # Strategy start time (HH:MM)
EXIT_TIME = "14:00"   # Exit time on expiry day (HH:MM)

# ===== Stop Loss / Target =====
TRAIL_START_PROFIT = 300  # Profit after which trailing starts
TRAIL_BUFFER = 50         # Buffer for trailing SL
TRAIL_STEP = 1            # Trail step amount

# ===== File Paths =====
TOKEN_FILE = "token.txt"
PAUSE_FILE = "pause.txt"