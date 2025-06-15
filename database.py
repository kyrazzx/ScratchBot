# ScratchBot v1.4.0
import sqlite3
import time
import logging

class Database:
    def __init__(self, db_file):
        try:
            self.conn = sqlite3.connect(db_file)
            self.cursor = self.conn.cursor()
            self._create_tables()
            logging.info("Database connection successful.")
        except sqlite3.Error as e:
            logging.critical(f"Database connection failed: {e}")
            raise

    def _create_tables(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS comments (
                id INTEGER PRIMARY KEY
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS gifts (
                author TEXT PRIMARY KEY,
                target TEXT NOT NULL
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_cooldowns (
                username TEXT PRIMARY KEY,
                last_command_timestamp REAL NOT NULL
            )
        """)
        self.conn.commit()

    def is_comment_seen(self, comment_id):
        self.cursor.execute("SELECT 1 FROM comments WHERE id = ?", (comment_id,))
        return self.cursor.fetchone() is not None

    def add_seen_comments(self, comment_ids):
        if not comment_ids:
            return
        try:
            self.cursor.executemany("INSERT OR IGNORE INTO comments (id) VALUES (?)", [(id,) for id in comment_ids])
            self.conn.commit()
        except sqlite3.Error as e:
            logging.error(f"Failed to add seen comments to DB: {e}")

    def has_sent_gift(self, author):
        self.cursor.execute("SELECT 1 FROM gifts WHERE author = ?", (author,))
        return self.cursor.fetchone() is not None

    def add_gift(self, author, target):
        try:
            self.cursor.execute("INSERT INTO gifts (author, target) VALUES (?, ?)", (author, target))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            logging.error(f"Failed to add gift to DB for {author}: {e}")
            return False

    def is_user_on_cooldown(self, username, cooldown_duration):
        self.cursor.execute("SELECT last_command_timestamp FROM user_cooldowns WHERE username = ?", (username,))
        result = self.cursor.fetchone()
        if result:
            time_since_last_command = time.time() - result[0]
            if time_since_last_command < cooldown_duration:
                return True
        return False

    def update_user_cooldown(self, username):
        timestamp = time.time()
        self.cursor.execute(
            "INSERT OR REPLACE INTO user_cooldowns (username, last_command_timestamp) VALUES (?, ?)",
            (username, timestamp)
        )
        self.conn.commit()

    def close(self):
        if self.conn:
            self.conn.close()
            logging.info("Database connection closed.")
    
    def delete_gift_by_author(self, author):
        try:
            self.cursor.execute("SELECT 1 FROM gifts WHERE author = ?", (author,))
            if self.cursor.fetchone() is None:
                return False

            self.cursor.execute("DELETE FROM gifts WHERE author = ?", (author,))
            self.conn.commit()
            return self.cursor.rowcount > 0
        except sqlite3.Error as e:
            logging.error(f"Failed to delete gift from DB for {author}: {e}")
            return False