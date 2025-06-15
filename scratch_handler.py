# ScratchBot v1.4.0
import scratchattach as scratch3
import logging
import time

class ScratchHandler:
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.session = None
        self.project = None

    def _login(self):
        try:
            self.session = scratch3.login(self.username, self.password)
            logging.info("Login to Scratch successful.")
            return True
        except Exception as e:
            logging.error(f"Login to Scratch failed: {e}")
            return False

    def connect_to_project(self, project_id):
        while not self.session:
            if not self._login():
                logging.info("Retrying login in 30 seconds.")
                time.sleep(30)
        try:
            self.project = self.session.connect_project(project_id)
            logging.info(f"Connected to project: {self.project.title}")
            return True
        except Exception as e:
            logging.error(f"Failed to connect to project {project_id}: {e}")
            return False

    def reconnect(self, project_id):
        logging.warning("Reconnecting...")
        self.session = None
        self.project = None
        time.sleep(10)
        return self.connect_to_project(project_id)

    def get_comments(self, limit=20):
        try:
            return self.project.comments(limit=limit)
        except Exception as e:
            logging.error(f"Failed to fetch comments: {e}")
            return []

    def reply_to_comment(self, comment, content):
        try:
            comment.reply(content)
            return "ok"
        except Exception as e:
            err = str(e).lower()
            if "forbidden" in err:
                logging.error("Reply forbidden. Session may be invalid.")
                return "forbidden"
            elif "flood" in err or "rejected" in err:
                logging.warning(f"Flood error on comment {comment.id}. Retrying later.")
                return "flood"
            elif "expecting value" in err:
                logging.warning(f"JSON decode error on comment {comment.id}, assuming success.")
                return "ok"
            else:
                logging.error(f"Unexpected error on reply to {comment.id}: {e}")
                return "error"

    def follow_user(self, username):
        try:
            user = self.session.connect_user(username)
            user.follow()
            logging.info(f"Successfully followed {username}.")
            return True
        except Exception as e:
            logging.error(f"Failed to follow {username}: {e}")
            if "forbidden" in str(e).lower():
                self.reconnect(self.project.id)
            return False

    def is_following(self, username):
        try:
            bot_user = self.session.connect_user(self.username)
            return username in bot_user.following()
        except Exception as e:
            logging.error(f"Could not check following status for {username}: {e}")
            return False

    def user_exists(self, username):
        try:
            self.session.connect_user(username)
            return True
        except Exception:
            return False