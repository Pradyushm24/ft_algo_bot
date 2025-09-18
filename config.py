# config.py
# Flattrade API Configuration

# ===== API Credentials =====
API_KEY = ""
API_SECRET = ""
CLIENT_ID = 

# ===== TOTP (Authenticator App Secret) =====
TOTP_SECRET = 

# ===== Trading Settings =====
LOT_SIZE = 65
SYMBOL = "FINNI"
EXCHANGE = "NFO"

# ===== Time Settings =====
START_TIME = ""  # Strategy start time (HH:MM)
EXIT_TIME = "   # Exit time on expiry day (HH:MM)

# ===== Stop Loss / Target =====
TRAIL_START_PROFIT =  # Profit after which trailing starts
TRAIL_BUFFER =         # Buffer for trailing SL
TRAIL_STEP =           # Trail step amount

# ===== File Paths =====
TOKEN_FILE = "token.txt"
PAUSE_FILE = "pause.txt"
