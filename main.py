# ScratchBot v1.3.9 | Beta version
__version__ = "1.3.9"

import requests, re, os, sys
import time, json, warnings
from collections import deque
from colorama import Fore
import scratchattach as scratch3
from dotenv import load_dotenv

load_dotenv()

GITHUB_RAW_URL = "https://raw.githubusercontent.com/kyrazzx/ScratchBot/main/main.py"
LOCAL_FILE = os.path.abspath(__file__)

# === AUTO UPDATE ===
def getversioncode(code):
    match = re.search(r'__version__\s*=\s*["\']([\d\.]+)["\']', code)
    return match.group(1) if match else None

def extcfgblock(code):
    match = re.search(r'(# === CONFIGURATION ===\n)(.*?)(\n# === SETUP ===)', code, re.DOTALL)
    return (match.group(2).strip() if match else None), match.group(1) if match else "", match.group(3) if match else ""

def repcfgblock(code, new_config, config_start, config_end):
    pattern = r'(# === CONFIGURATION ===\n)(.*?)(\n# === SETUP ===)'
    return re.sub(pattern, f"{config_start}{new_config}\n{config_end}", code, flags=re.DOTALL)

def replace_version(code, version):
    return re.sub(r'__version__\s*=\s*["\'].*?["\']', f'__version__ = "{version}"', code)

def compare_versions(v1, v2):
    def parse(v): return list(map(int, v.split("."))) + [0]*(3 - len(v.split(".")))
    return parse(v1) < parse(v2)

def check_for_updates():
    try:
        with open(LOCAL_FILE, "r", encoding="utf-8") as f:
            local_code = f.read()
        local_version = getversioncode(local_code)
        local_config, config_start, config_end = extcfgblock(local_code)
        response = requests.get(GITHUB_RAW_URL)
        if response.status_code == 200:
            remote_code = response.text
            remote_version = getversioncode(remote_code)
            if remote_version and local_version and compare_versions(local_version, remote_version):
                if not compare_versions(remote_version, "1.4.0"):
                    print(f"[⬆️] New version {remote_version} available (current: {local_version})")
                    print("📦 This new version break the current update system.")
                    print("🛠️ Please download manually the update on:")
                    print("👉 https://github.com/kyrazzx/ScratchBot")
                    return
                print(f"[⬆️] New version {remote_version} available (current: {local_version})")
                if local_config:
                    remote_code = repcfgblock(remote_code, local_config, config_start, config_end)
                remote_code = replace_version(remote_code, remote_version)
                with open(LOCAL_FILE, "w", encoding="utf-8") as f:
                    f.write(remote_code)
                print("[✅] Script updated! Restarting...")
                os.execv(sys.executable, [sys.executable] + sys.argv)
            else:
                print("[🆗] Already up to date.")
        else:
            print("[⚠️] Failed to fetch remote script.")
    except Exception as e:
        print(f"[❌] Auto-update error: {e}")

check_for_updates()

# === CONFIG ===
USERNAME = os.getenv("BOTUSERNAME")
PASSWORD = os.getenv("BOTPASSWORD")
PROJECT_ID = os.getenv("BOTPROJECT")
DATABASE_FILE = "gift.json"
SEEN_FILE = "comments.json"
CHECK_INTERVAL = 20
COOLDOWN_BETWEEN_ACTIONS = 10
MAX_RETRIES = 10

# === SETUP ===
warnings.filterwarnings('ignore', category=scratch3.LoginDataWarning)

if not USERNAME or not PASSWORD:
    print(Fore.RED + "❌ Username or password missing. Define them in your .env file.")
    sys.exit(1)

def login():
    try:
        session = scratch3.login(USERNAME, PASSWORD)
        print(Fore.GREEN + "[✅] Login successful.")
        return session
    except Exception as e:
        print(Fore.RED + f"[❌] Login failed: {e}")
        time.sleep(10)
        return login()

session = login()
project = session.connect_project(PROJECT_ID)

print(Fore.CYAN + f"Connected to project: {project.title}")
print(Fore.GREEN + f"[🤖] Bot online | v{__version__} | github.com/kyrazzx/ScratchBot")

# === DB ===
gift_db = {}
if os.path.exists(DATABASE_FILE):
    try:
        with open(DATABASE_FILE, "r") as f:
            gift_db = json.load(f)
    except Exception:
        gift_db = {}

seen_comments = set()
if os.path.exists(SEEN_FILE):
    try:
        with open(SEEN_FILE, "r") as f:
            seen_comments = set(json.load(f))
    except Exception:
        seen_comments = set()

def save_db():
    with open(DATABASE_FILE, "w") as f:
        json.dump(gift_db, f)

def save_seen_comments():
    with open(SEEN_FILE, "w") as f:
        json.dump(list(seen_comments), f)

# === QUEUE ===
comment_queue = deque()

def requeue(comment, retries):
    retries += 1
    if retries < MAX_RETRIES:
        print(Fore.YELLOW + f"🔁 Requeuing comment {comment.id} (retry {retries})")
        comment_queue.append((comment, retries))
    else:
        print(Fore.RED + f"⚠ Skipping comment {comment.id} after {MAX_RETRIES} retries.")

def reply(comment, content):
    try:
        comment.reply(content)
        return "ok"
    except Exception as e:
        err = str(e)
        if "Forbidden" in err:
            print(Fore.RED + "🚫 Forbidden error, reconnecting...")
            reconnect()
            return "forbidden"
        elif "flood" in err or "rejected" in err:
            print(Fore.YELLOW + f"⏳ Flood error on {comment.id}")
            return "flood"
        elif "Expecting value" in err:
            print(Fore.YELLOW + f"⚠ JSON decode error on {comment.id}, assuming success.")
            return "ok"
        else:
            print(Fore.RED + f"❌ Unexpected error on reply: {e}")
            return "error"

def already_follows(username):
    try:
        user = session.connect_user(USERNAME)
        return username in user.following()
    except:
        return False

def follow_user(username):
    try:
        if not is_valid_username(username):
            print(Fore.RED + f"⚠ Invalid username: {username}")
            return False
        user = session.connect_user(username)
        user.follow()
        return True
    except Exception as e:
        print(Fore.RED + f"❌ Follow failed: {e}")
        if "Forbidden" in str(e):
            reconnect()
        return False

def reconnect():
    global session, project
    try:
        session = login()
        project = session.connect_project(PROJECT_ID)
        print(Fore.GREEN + "[🔄] Reconnected successfully.")
    except Exception as e:
        print(Fore.RED + f"[❌] Reconnection failed: {e}")
        time.sleep(30)
        reconnect()

# === SECURITY (avoid injection) ===
def is_valid_username(name):
    return re.match(r"^[a-zA-Z0-9_\-]{3,20}$", name) is not None

def is_safe_command(content):
    return re.match(r'^\+\w+(\s[\w\-]{3,20})?$', content.strip()) is not None

# === MAIN ===
while True:
    try:
        comments = project.comments(limit=10)
        for comment in reversed(comments):
            content = comment.content.strip()
            if comment.id in seen_comments or not content.startswith("+"):
                continue
            if not is_safe_command(content):
                print(Fore.RED + f"🚫 Ignored suspicious comment: {content}")
                seen_comments.add(comment.id)
                save_seen_comments()
                continue
            seen_comments.add(comment.id)
            comment_queue.append((comment, 0))
        if comment_queue:
            comment, retries = comment_queue.popleft()
            content = comment.content.strip()
            author = comment.author().username
            print(Fore.BLUE + f"📨 Handling comment {comment.id} by {author} | Retry {retries}")
            result = "ok"
            if content.lower() == "+follow":
                if already_follows(author):
                    result = reply(comment, "I already follow you.")
                else:
                    if follow_user(author):
                        time.sleep(3)
                        result = reply(comment, "You are now followed by me!")
                    else:
                        result = reply(comment, "Follow failed.")
            elif content.lower().startswith("+gift "):
                parts = content.split()
                if len(parts) != 2:
                    result = reply(comment, "Usage: +gift username")
                else:
                    target = parts[1]
                    if not is_valid_username(target):
                        result = reply(comment, "Invalid username format.")
                    elif author in gift_db:
                        result = reply(comment, "You already sent a gift.")
                    else:
                        try:
                            session.connect_user(target)
                            if already_follows(target):
                                result = reply(comment, f"{target} is already followed.")
                            else:
                                if follow_user(target):
                                    time.sleep(3)
                                    result = reply(comment, f"{target} is now followed.")
                                    if result == "ok":
                                        gift_db[author] = target
                                        save_db()
                                else:
                                    result = reply(comment, "Failed to follow user.")
                        except:
                            result = reply(comment, "User does not exist.")
            else:
                result = reply(comment, "Unknown command.")
            if result in ("forbidden", "flood", "error"):
                requeue(comment, retries)
            save_seen_comments()
            time.sleep(COOLDOWN_BETWEEN_ACTIONS)
        else:
            time.sleep(CHECK_INTERVAL)
    except Exception as e:
        print(Fore.RED + f"[‼️] Runtime error: {e}")
        time.sleep(CHECK_INTERVAL)
