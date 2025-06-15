# ScratchBot v1.4.0
import os
import sys
import json
import logging
from dotenv import load_dotenv

load_dotenv()

# --- ENV ---
USERNAME = os.getenv("BOTUSERNAME")
PASSWORD = os.getenv("BOTPASSWORD")
PROJECT_ID = os.getenv("BOTPROJECT")
ADMIN_USERNAMES = [name.strip() for name in os.getenv("ADMIN_USERNAMES", "").split(',') if name.strip()]

# --- SETTINGS ---
CHECK_INTERVAL = 20
COOLDOWN_BETWEEN_ACTIONS = 5
MAX_RETRIES = 5
USER_COMMAND_COOLDOWN = 60
SAVE_INTERVAL = 300

# --- FILE PATHS ---
DATABASE_FILE = "bot_database.sqlite"
CONFIG_FILE = "config.json"
LOCAL_MAIN_FILE = os.path.abspath("main.py")

# --- DO NOT EDIT THIS LINK ---
GITHUB_RAW_URL_MAIN = "https://raw.githubusercontent.com/kyrazzx/ScratchBot/main/main.py"

def load_responses():
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            config_data = json.load(f)
            config_data["bot_responses"].setdefault("resetgift_success", "The gift from {target} has been successfully reset. They can now send a new one.")
            config_data["bot_responses"].setdefault("resetgift_fail", "Could not find a gift sent by the user {target}.")
            config_data["bot_responses"].setdefault("resetgift_usage", "Incorrect usage. Try: +resetgift <username>")
            config_data["bot_responses"].setdefault("admin_only_command", "This command can only be used by an administrator.")
            return config_data["bot_responses"]
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logging.critical(f"Could not load or parse {CONFIG_FILE}: {e}")
        sys.exit(1)

def validate_env_vars():
    if not all([USERNAME, PASSWORD, PROJECT_ID]):
        logging.critical("USERNAME, PASSWORD, or PROJECT_ID not set in .env file.")
        sys.exit(1)
    if not ADMIN_USERNAMES:
        logging.warning("ADMIN_USERNAMES is not set in the .env file. Admin commands will be disabled.")
RESPONSES = load_responses()
validate_env_vars()