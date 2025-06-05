# ScratchBot v1.2 | Beta version
from colorama import Fore
import scratchattach as scratch3
import time
import json
import os
import warnings
from collections import deque

# === CONFIGURATION ===
USERNAME = "YOUR_BOT_USERNAME" # Put your bot username
PASSWORD = "YOUR_BOT_PASSWORD" # Put your bot password
PROJECT_ID = 1234567890 # Put your real project ID that you wanna monitor
DATABASE_FILE = "gift.json"
SEEN_FILE = "comments.json"
CHECK_INTERVAL = 20
COOLDOWN_BETWEEN_ACTIONS = 10
MAX_RETRIES = 10

# === SETUP ===
warnings.filterwarnings('ignore', category=scratch3.LoginDataWarning)

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
print(Fore.GREEN + "[🤖] Bot online | github.com/kyrazzx/ScratchBot")

# === DATABASE ===
gift_db = {}
if os.path.exists(DATABASE_FILE):
    with open(DATABASE_FILE, "r") as f:
        gift_db = json.load(f)

seen_comments = set()
if os.path.exists(SEEN_FILE):
    try:
        with open(SEEN_FILE, "r") as f:
            seen_comments = set(json.load(f))
    except Exception:
        pass

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
        if len(comment_queue) == 0:
            print(Fore.YELLOW + "🕐 Waiting 5s before retry (only one comment in queue)...")
            time.sleep(5)
        comment_queue.append((comment, retries))
    else:
        print(Fore.RED + f"⚠ Skipping comment {comment.id} after {MAX_RETRIES} retries.")

def reply(comment, content):
    try:
        comment.reply(content)
        return "ok"
    except Exception as e:
        err_str = str(e)
        if "Forbidden" in err_str:
            print(Fore.RED + f"🚫 Forbidden error on reply. Reconnecting...")
            reconnect()
            return "forbidden"
        elif "isFlood" in err_str or "rejected" in err_str:
            print(Fore.YELLOW + f"⏳ Flood error on reply {comment.id}")
            return "flood"
        elif "Expecting value" in err_str:
            print(Fore.YELLOW + f"⚠ JSON decode error on reply {comment.id} ignored, assuming success.")
            return "ok"
        else:
            print(Fore.RED + f"❌ Error replying to {comment.id}: {e}")
            return "error"

def already_follows(username):
    try:
        user = session.connect_user(USERNAME)
        return username in user.following()
    except Exception:
        return False

def follow_user(username):
    try:
        user = session.connect_user(username)
        user.follow()
        return True
    except Exception as e:
        if "Forbidden" in str(e):
            print(Fore.RED + f"🚫 Forbidden while following. Reconnecting...")
            reconnect()
        print(Fore.RED + f"❌ Follow error: {e}")
        return False

def reconnect():
    global session, project
    try:
        session = login()
        project = session.connect_project(PROJECT_ID)
        print(Fore.GREEN + "[🔄] Reconnected successfully.")
        time.sleep(10)
    except Exception as e:
        print(Fore.RED + f"[❌] Reconnection failed: {e}")
        time.sleep(30)
        reconnect()

# === MAIN ===
while True:
    try:
        comments = project.comments(limit=20)
        for comment in reversed(comments):
            if comment.id not in seen_comments:
                seen_comments.add(comment.id)
                comment_queue.append((comment, 0))
        if comment_queue:
            comment, retries = comment_queue.popleft()
            content = comment.content.strip()
            author = comment.author().username
            print(Fore.BLUE + f"📨 Handling comment {comment.id} by {author} | Retry: {retries}")
            if content.lower() == "+follow":
                if already_follows(author):
                    result = reply(comment, "I already follow you...")
                else:
                    if follow_user(author):
                        time.sleep(5)
                        result = reply(comment, "You are now followed by me!")
                    else:
                        result = reply(comment, "Failed to follow you, something went wrong.")
            elif content.lower().startswith("+gift "):
                parts = content.split()
                if len(parts) != 2:
                    result = reply(comment, "Invalid syntax. Use: +gift username")
                else:
                    target = parts[1]
                    if author in gift_db:
                        result = reply(comment, "You already sent a gift to someone else...")
                    else:
                        try:
                            session.connect_user(target)
                        except Exception:
                            result = reply(comment, f"{target} does not exist...")
                        else:
                            if already_follows(target):
                                result = reply(comment, f"{target} is already followed by me!")
                            else:
                                if follow_user(target):
                                    time.sleep(5)
                                    result = reply(comment, f"{target} is now followed by me")
                                    if result == "ok":
                                        gift_db[author] = target
                                        save_db()
                                    else:
                                        print(Fore.YELLOW + f"⚠ Gift follow succeeded but reply failed.")
                                else:
                                    result = reply(comment, "Failed to follow. Something went wrong.")
            else:
                print(Fore.YELLOW + f"⚠ Unknown command: {content}")
                result = "ok"
            if result in ("flood", "forbidden", "error"):
                requeue(comment, retries)
            save_seen_comments()
            time.sleep(COOLDOWN_BETWEEN_ACTIONS)
        else:
            time.sleep(CHECK_INTERVAL)
    except Exception as e:
        print(Fore.RED + f"[‼️] Unexpected error: {e}")
        time.sleep(CHECK_INTERVAL)
