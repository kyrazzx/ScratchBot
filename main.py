# ScratchBot v1.1 | Beta version
import scratchattach as scratch3
import time
import json
import os
import warnings

warnings.filterwarnings('ignore', category=scratch3.LoginDataWarning)

USERNAME = "null" # Edit with the username of the bot
PASSWORD = "null" # Edit with the password of the bot
PROJECT_ID = 132456789 # Edit with the project ID you wanna monitor
GIFT_DB_FILE = "gift_db.json"
SEEN_COMMENTS_FILE = "seen_comments.json"
CHECK_INTERVAL = 10

session = scratch3.login(USERNAME, PASSWORD)
project = session.connect_project(PROJECT_ID)

print(f"Connected project : {project.title}")
print("[✅] Bot is ready | ScratchBot v1.1 | Download latest version: github.com/kyrazzx/ScratchBot")

gift_db = {}
if os.path.exists(GIFT_DB_FILE):
    with open(GIFT_DB_FILE, "r") as f:
        gift_db = json.load(f)

seen_comments = set()
if os.path.exists(SEEN_COMMENTS_FILE):
    with open(SEEN_COMMENTS_FILE, "r") as f:
        seen_comments = set(json.load(f))

def save_db():
    with open(GIFT_DB_FILE, "w") as f:
        json.dump(gift_db, f)

def save_seen():
    with open(SEEN_COMMENTS_FILE, "w") as f:
        json.dump(list(seen_comments), f)

def already_follows(username):
    try:
        my_user = session.connect_user(USERNAME)
        following = my_user.following()
        return username in following
    except Exception as e:
        print(f"Error in already_follows {username}: {e}")
        return False

def follow_user(username):
    try:
        user = session.connect_user(username)
        user.follow()
        return True
    except Exception as e:
        print(f"Error while aptempting to follow {username}: {e}")
        return False

def reply(comment, content):
    try:
        comment.reply(content)
    except Exception as e:
        print(f"Error replying to {comment.author()}: {e}")

while True:
    try:
        comments = project.comments(limit=20)
        for comment in comments:
            if comment.id in seen_comments:
                continue
            seen_comments.add(comment.id)
            content = comment.content.strip()
            author = comment.author()
            if content.lower() == "+follow":
                if already_follows(author):
                    reply(comment, "I already follow you...")
                else:
                    if follow_user(author):
                        reply(comment, "You are now followed by me!")
                    else:
                        reply(comment, "Failed to follow you, something went wrong.")
            elif content.lower().startswith("+gift "):
                parts = content.strip().split(maxsplit=1)
                if len(parts) != 2:
                    reply(comment, "Invalid syntax. Use: +gift username")
                    continue
                target = parts[1].strip()
                if author in gift_db:
                    reply(comment, "You already sent a gift to someone else...")
                    continue
                try:
                    target_user = session.connect_user(target)
                except Exception:
                    reply(comment, f"{target} does not exist...")
                    continue
                if already_follows(target):
                    reply(comment, f"{target} is already followed by me!")
                    continue
                if follow_user(target):
                    reply(comment, f"{target} is now followed by me")
                    gift_db[author] = target
                    save_db()
                else:
                    reply(comment, "Failed to follow. Something went wrong.")
        save_seen()

    except Exception as e:
        print("Error:", e)

    time.sleep(CHECK_INTERVAL)
