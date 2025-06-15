# ScratchBot v1.4.0
import re

def is_valid_username(name):
    return re.match(r"^[a-zA-Z0-9_\-]{3,20}$", name) is not None

def is_safe_command(content):
    return re.match(r'^\+\w+(\s[\w\-]{3,20})?$', content.strip()) is not None