# ScratchBot v1.4.0
import logging
from utils import is_valid_username

COOLDOWN_COMMANDS = ["+follow", "+gift"]
ADMIN_COMMANDS = ["+resetgift"]

def process_command(comment, scratch_handler, db, config):
    content = comment.content.strip().lower()
    author = comment.author().username
    parts = content.split()
    command = parts[0]
    responses = config.RESPONSES
    if command in ADMIN_COMMANDS:
        if author not in config.ADMIN_USERNAMES:
            logging.warning(f"Non-admin user '{author}' tried to use command: {command}")
            return responses["admin_only_command"]
        if command == "+resetgift":
            return handle_reset_gift(parts, db, responses)
    if command == "+help":
        return responses["help_message"]
    if command in COOLDOWN_COMMANDS:
        if db.is_user_on_cooldown(author, config.USER_COMMAND_COOLDOWN):
            logging.info(f"User {author} is on cooldown for command '{command}'.")
            return responses["spam_cooldown"]
        reply_message = ""
        if command == "+follow":
            reply_message = handle_follow(author, scratch_handler, responses)
        elif command == "+gift":
            if len(parts) != 2:
                reply_message = responses["gift_usage"]
            else:
                target = parts[1]
                reply_message = handle_gift(author, target, scratch_handler, db, responses) 
        if reply_message in [responses["follow_success"], responses["gift_success"]]:
            db.update_user_cooldown(author)
            logging.info(f"Cooldown updated for user {author} after successful command '{command}'.")
        return reply_message 
    return responses["unknown_command"]

def handle_reset_gift(parts, db, responses):
    if len(parts) != 2:
        return responses["resetgift_usage"]
    target_user = parts[1]
    if not is_valid_username(target_user):
        return responses["gift_invalid_username"].format(target=target_user)
    logging.info(f"Admin is attempting to reset gift for user '{target_user}'.")
    if db.delete_gift_by_author(target_user):
        logging.info(f"Successfully reset gift for '{target_user}'.")
        return responses["resetgift_success"].format(target=target_user)
    else:
        logging.warning(f"Failed to reset gift for '{target_user}' - no gift found in database.")
        return responses["resetgift_fail"].format(target=target_user)

def handle_follow(author, scratch_handler, responses):
    if scratch_handler.is_following(author):
        return responses["follow_already_following"]
    else:
        if scratch_handler.follow_user(author):
            return responses["follow_success"]
        else:
            return responses["follow_fail"]

def handle_gift(author, target, scratch_handler, db, responses):
    if not is_valid_username(target):
        return responses["gift_invalid_username"].format(target=target)

    if db.has_sent_gift(author):
        return responses["gift_already_sent"]

    if not scratch_handler.user_exists(target):
        return responses["gift_user_not_exist"].format(target=target)

    if scratch_handler.is_following(target):
        return responses["gift_target_already_followed"].format(target=target)

    if scratch_handler.follow_user(target):
        if db.add_gift(author, target):
            return responses["gift_success"].format(target=target)
        else:
            logging.error(f"Followed {target} but failed to save gift from {author} to DB.")
            return responses["gift_fail"].format(target=target)
    else:
        return responses["gift_fail"].format(target=target)