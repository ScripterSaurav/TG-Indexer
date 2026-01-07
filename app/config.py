# config.py - Simplified version
from pathlib import Path
import tempfile
import traceback
import json
import sys
import os
from dotenv import load_dotenv

# Load environment variables from .env or either config.env file if present
load_dotenv()

# --- Port validation ---
try:
    port = int(os.environ.get("PORT", "8080"))
except Exception as e:
    print(e)
    port = -1
if not 1 <= port <= 65535:
    print("Please make sure the PORT environment variable is an integer between 1 and 65535")
    sys.exit(1)

# --- Telegram API credentials ---
try:
    api_id = int(os.environ["API_ID"])
    api_hash = os.environ["API_HASH"]
except (KeyError, ValueError):
    traceback.print_exc()
    print("\n\nPlease set the API_ID and API_HASH environment variables correctly")
    print("You can get your own API keys at https://my.telegram.org/apps")
    sys.exit(1)

# --- Index settings ---
try:
    index_settings_str = os.environ["INDEX_SETTINGS"].strip()
    index_settings = json.loads(index_settings_str)
except Exception:
    traceback.print_exc()
    print("\n\nPlease set the INDEX_SETTINGS environment variable correctly")
    sys.exit(1)

# --- User session ---
try:
    session_string = os.environ["SESSION_STRING"]
except (KeyError, ValueError):
    traceback.print_exc()
    print("\n\nPlease set the SESSION_STRING environment variable correctly")
    sys.exit(1)

# --- Basic runtime config ---
host = os.environ.get("HOST", "0.0.0.0")
debug = bool(os.environ.get("DEBUG"))
block_downloads = bool(os.environ.get("BLOCK_DOWNLOADS"))
results_per_page = int(os.environ.get("RESULTS_PER_PAGE", "20"))

logo_folder = Path(os.path.join(tempfile.gettempdir(), "logo"))
logo_folder.mkdir(parents=True, exist_ok=True)

username = os.environ.get("TGINDEX_USERNAME", "")
password = os.environ.get("TGINDEX_PASSWORD", "")
SHORT_URL_LEN = int(os.environ.get("SHORT_URL_LEN", 3))
authenticated = bool(username and password)
SESSION_COOKIE_LIFETIME = int(os.environ.get("SESSION_COOKIE_LIFETIME") or "60")

# --- Secret key ---
try:
    SECRET_KEY = os.environ["SECRET_KEY"]
    if len(SECRET_KEY) != 32:
        raise ValueError("SECRET_KEY should be exactly 32 characters long")
except (KeyError, ValueError):
    if authenticated:
        traceback.print_exc()
        print("\n\nPlease set the SECRET_KEY environment variable correctly")
        sys.exit(1)
    else:
        SECRET_KEY = "default_secret_key_change_in_production_32_chars!"

# --- Token validation for downloads/streams ---
token_validation_enabled = os.environ.get("TOKEN_VALIDATION_ENABLED", "true").strip().lower() == "true"
token_lifetime = int(os.environ.get("TOKEN_LIFETIME", "3600"))  # 60 minutes (1 hour) default

# Use the same SECRET_KEY for tokens - no need for separate token secret
# This ensures consistency and reduces configuration complexity

# --- Chat Lock Configuration ---
chat_lock_enabled = os.environ.get("CHAT_LOCK_ENABLED", "false").strip().lower() == "true"

# Per-channel passwords as JSON string: {"chat_id": "password"}
channel_passwords_str = os.environ.get("CHANNEL_PASSWORDS", "{}")
try:
    raw_channel_passwords = json.loads(channel_passwords_str)
except json.JSONDecodeError:
    raw_channel_passwords = {}

# Convert channel passwords to handle both formats (with and without -100 prefix)
channel_passwords = {}
for chat_id_str, chat_password in raw_channel_passwords.items():
    # Remove -100 prefix if present for internal storage
    if chat_id_str.startswith('-100'):
        clean_chat_id = chat_id_str[4:]
    else:
        clean_chat_id = chat_id_str
    channel_passwords[clean_chat_id] = chat_password

chat_lock_session_lifetime = int(os.environ.get("CHAT_LOCK_SESSION_LIFETIME", "30")) # minutes

# Helper functions
def is_chat_locked(chat_id):
    # Convert chat_id to string and remove -100 prefix if present
    chat_id_str = str(chat_id)
    if chat_id_str.startswith('-100'):
        chat_id_str = chat_id_str[4:]

    result = chat_id_str in channel_passwords

    if debug:
        print(f"[DEBUG] is_chat_locked: chat={chat_id}, normalized={chat_id_str}, locked={result}")

    return result


def get_chat_password(chat_id):
    # Convert chat_id to string and remove -100 prefix if present
    chat_id_str = str(chat_id)
    if chat_id_str.startswith('-100'):
        chat_id_str = chat_id_str[4:]

    chat_password = channel_passwords.get(chat_id_str)

    if debug:
        masked = '*' * len(chat_password) if chat_password else 'None'
        print(f"[DEBUG] get_chat_password: chat={chat_id}, normalized={chat_id_str}, password={masked}")

    return chat_password
