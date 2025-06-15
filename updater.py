# ScratchBot v1.4.0
import requests
import re
import logging
from config import GITHUB_RAW_URL_MAIN, LOCAL_MAIN_FILE

def get_version_from_code(code):
    match = re.search(r'__version__\s*=\s*["\']([\d\.]+)["\']', code)
    return match.group(1) if match else None

def compare_versions(v1, v2):
    def parse(v):
        return list(map(int, v.split(".")))
    return parse(v1) < parse(v2)

def check_for_updates():
    logging.info("Checking for updates...")
    try:
        with open(LOCAL_MAIN_FILE, "r", encoding="utf-8") as f:
            local_code = f.read()
        local_version = get_version_from_code(local_code)

        if not local_version:
            logging.warning("Could not determine local version. Skipping update check.")
            return

        response = requests.get(GITHUB_RAW_URL_MAIN)
        if response.status_code == 200:
            remote_code = response.text
            remote_version = get_version_from_code(remote_code)

            if remote_version and compare_versions(local_version, remote_version):
                logging.warning(f"New version {remote_version} available (current: {local_version}).")
                logging.warning("Please update the bot manually by running 'git pull' or downloading from GitHub.")
            else:
                logging.info("Bot is up to date.")
        else:
            logging.warning(f"Failed to fetch remote version. Status: {response.status_code}")
    except Exception as e:
        logging.error(f"An error occurred during update check: {e}")