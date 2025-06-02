# ScratchBot v1.1 | Beta version
import scratchattach as scratch3
import time
import json
import os
import warnings

warnings.filterwarnings('ignore', category=scratch3.LoginDataWarning)

USERNAME = "YOUR_BOT_USERNAME" # Put your bot username
PASSWORD = "YOUR_BOT_PASSWORD" # Put your bot password
PROJECT_ID = 123456789 # Put your real project ID that you wanna monitor
DATABASE_FILE = "gift_db.json"
SEEN_FILE = "seen_comments.json"
CHECK_INTERVAL = 10

session = scratch3.login(USERNAME, PASSWORD)
project = session.connect_project(PROJECT_ID)

print(f"Projet connecté : {project.title}")
print("Bot en ligne...")

if os.path.exists(DATABASE_FILE):
    with open(DATABASE_FILE, "r") as f:
        gift_db = json.load(f)
else:
    gift_db = {}

if os.path.exists(SEEN_FILE):
    try:
        with open(SEEN_FILE, "r") as f:
            seen_comments = set(json.load(f))
    except Exception:
        seen_comments = set()
else:
    seen_comments = set()

def save_db():
    with open(DATABASE_FILE, "w") as f:
        json.dump(gift_db, f)

def save_seen_comments():
    with open(SEEN_FILE, "w") as f:
        json.dump(list(seen_comments), f)

def reply(comment, content):
    try:
        comment.reply(content)
    except Exception as e:
        print(f"Erreur en répondant au commentaire {comment.id}: {e}")

def already_follows(username):
    try:
        user = session.connect_user(USERNAME)
        following = user.following()
        return username in following
    except Exception:
        return False

def follow_user(username):
    try:
        user = session.connect_user(username)
        user.follow()
        return True
    except Exception as e:
        print(f"Erreur lors du follow de {username}: {e}")
        return False

while True:
    try:
        comments = project.comments(limit=20)
        for comment in comments:
            if comment.id in seen_comments:
                continue
            seen_comments.add(comment.id)

            content = comment.content.strip()
            author_obj = comment.author()  # appeler la méthode pour obtenir l'objet user
            author = author_obj.username

            if content.lower() == "+follow":
                if already_follows(author):
                    reply(comment, "I already follow you...")
                else:
                    if follow_user(author):
                        reply(comment, "You are now followed by me!")
                    else:
                        reply(comment, "Failed to follow you, something went wrong.")

            elif content.lower().startswith("+gift "):
                parts = content.split()
                if len(parts) != 2:
                    reply(comment, "Invalid syntax. Use: +gift username")
                    continue

                target = parts[1]

                if author in gift_db:
                    reply(comment, "You already sent a gift to someone else...")
                    continue

                try:
                    _ = session.connect_user(target)
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

        save_seen_comments()
    except Exception as e:
        print("Erreur:", e)

    time.sleep(CHECK_INTERVAL)
