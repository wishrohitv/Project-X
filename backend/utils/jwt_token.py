from typing import Any

from modules import datetime, jwt, timedelta
from settings import Settings


def decode_jwt_token(client_token):
    """
    Decodes a JWT token using the application's hash key.
    exception should be handled by the caller.
    Args:
        client_token (str): The JWT token to decode.

    Returns:
        dict: The decoded token payload.
    """
    data = jwt.decode(jwt=client_token, key=Settings.JWT_HASH_KEY, algorithms="HS256")
    return data


def generate_jwt_token(user_data: dict[str, Any], expire_in_minute: int):
    current_time = datetime.now() + timedelta(minutes=expire_in_minute)
    unix_timestamp = current_time.timestamp()  # expiry time

    payload = {"payload": user_data, "exp": int(unix_timestamp)}

    token = jwt.encode(payload, Settings.JWT_HASH_KEY, algorithm="HS256")
    return token
