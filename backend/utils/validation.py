from modules import re


def get_usernames(text: str) -> list:
    """
    Extracts all mentioned usernames from the given text.
    Usernames are expected to be prefixed with '@' and
    consist of word characters (letters, digits, and underscores).
    The function returns a list of extracted usernames.
    """
    pattern = r"@(\w+)"
    matches = re.findall(pattern, text)
    return matches


def validate_email(email: str) -> bool:
    pass


def validate_password(password: str) -> bool:
    pass


def validate_username(username: str) -> bool:
    pass
