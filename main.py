# ScratchBot v1.4.0
__version__ = "1.4.0"

import os
import sys
import time

def bootstrap_script():
    required_files = [
        "commands.py", "config.py", "database.py", "scratch_handler.py",
        "updater.py", "utils.py", "requirements.txt"
    ]
    files_are_present = all(os.path.exists(f) for f in required_files)
    if files_are_present:
        return
    print("[SETUP] Essential files are missing. Attempting self-installation...")
    print("[WARNING] This will download the latest version from GitHub and overwrite local files.")
    time.sleep(2)

    try:
        import requests
    except ImportError:
        print("[SETUP] 'requests' library not found. Attempting to install it...")
        try:
            import subprocess
            subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"],
                                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            import requests
            print("[SETUP] 'requests' installed successfully.")
        except Exception as e:
            print(f"[FATAL ERROR] Failed to install 'requests'.")
            print("Please install it manually by running: pip install requests")
            print(f"Details: {e}")
            sys.exit(1)
    repo_zip_url = "https://github.com/kyrazzx/ScratchBot/archive/refs/heads/main.zip"
    try:
        print(f"[SETUP] Downloading repository from {repo_zip_url}...")
        response = requests.get(repo_zip_url, stream=True)
        response.raise_for_status()
        zip_content = response.content
        print("[SETUP] Download complete.")
    except Exception as e:
        print(f"[FATAL ERROR] Failed to download the repository.")
        print(f"Please download it manually from https://github.com/kyrazzx/ScratchBot")
        print(f"Details: {e}")
        sys.exit(1)
    import zipfile
    import io

    try:
        print("[SETUP] Extracting files...")
        with zipfile.ZipFile(io.BytesIO(zip_content)) as zf:
            root_folder = zf.namelist()[0]
            for member in zf.infolist():
                destination_path = member.filename.replace(root_folder, "", 1)
                if not destination_path:
                    continue
                zf.extract(member, path=".")
                if os.path.exists(destination_path):
                    os.remove(destination_path)
                os.rename(member.filename, destination_path)
        print("[SETUP] Files extracted successfully.")
    except Exception as e:
        print(f"[FATAL ERROR] Failed to extract files.")
        print(f"Please extract the repository manually.")
        print(f"Details: {e}")
        sys.exit(1)
    print("[SETUP] Installing required packages...")
    try:
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("[SETUP] All dependencies installed.")
    except Exception as e:
        print(f"[ERROR] Failed to install all dependencies from requirements.txt.")
        print("You may need to run 'pip install -r requirements.txt' manually.")
        print(f"Details: {e}")
    print("\n[SETUP] Installation complete! Restarting the bot now...")
    time.sleep(2)
    os.execv(sys.executable, [sys.executable] + sys.argv)

bootstrap_script()

import logging
import warnings
import scratchattach
from collections import deque
import config
import updater
from database import Database
from scratch_handler import ScratchHandler
from utils import is_safe_command
import commands

warnings.filterwarnings('ignore', category=scratchattach.LoginDataWarning)

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler("bot.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )

def main():
    setup_logging()
    logging.info(f"Starting ScratchBot v{__version__}")
    updater.check_for_updates()
    if not os.path.exists("config.json") or not os.path.exists(".env"):
        logging.critical("Configuration files (.env, config.json) not found.")
        logging.critical("Please create them by following the instructions in README.md.")
        sys.exit(1)
    db = Database(config.DATABASE_FILE)
    scratcher = ScratchHandler(config.USERNAME, config.PASSWORD)
    if not scratcher.connect_to_project(config.PROJECT_ID):
        sys.exit(1)
    comment_queue = deque()
    seen_comments_cache = set()
    last_db_save_time = time.time()

    try:
        while True:
            new_comments = scratcher.get_comments()
            for comment in reversed(new_comments):
                if comment.id in seen_comments_cache or not comment.content.startswith("+"):
                    continue
                if db.is_comment_seen(comment.id):
                    seen_comments_cache.add(comment.id)
                    continue
                if not is_safe_command(comment.content):
                    logging.warning(f"Ignored suspicious command from {comment.author().username}: {comment.content}")
                    seen_comments_cache.add(comment.id)
                    continue
                comment_queue.append((comment, 0))
                seen_comments_cache.add(comment.id)
            if comment_queue:
                comment, retries = comment_queue.popleft()
                author = comment.author().username
                logging.info(f"Processing command from {author}: {comment.content.strip()}")
                reply_message = commands.process_command(comment, scratcher, db, config)
                result = scratcher.reply_to_comment(comment, reply_message)
                if result in ("forbidden", "flood", "error"):
                    if retries < config.MAX_RETRIES:
                        logging.warning(f"Requeuing comment {comment.id} (retry {retries + 1})")
                        comment_queue.append((comment, retries + 1))
                    else:
                        logging.error(f"Skipping comment {comment.id} after {config.MAX_RETRIES} retries.")
                time.sleep(config.COOLDOWN_BETWEEN_ACTIONS)
            else:
                time.sleep(config.CHECK_INTERVAL)
            if time.time() - last_db_save_time > config.SAVE_INTERVAL:
                logging.info("Saving seen comments to database...")
                db.add_seen_comments(seen_comments_cache)
                seen_comments_cache.clear()
                last_db_save_time = time.time()
    except KeyboardInterrupt:
        logging.info("Bot shutting down by user request.")
    except Exception as e:
        logging.error(f"An unexpected error occurred in main loop: {e}", exc_info=True)
    finally:
        logging.info("Final save of seen comments before shutdown...")
        db.add_seen_comments(seen_comments_cache)
        db.close()
        logging.info("Shutdown complete.")

if __name__ == "__main__":
    main()