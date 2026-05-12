from typing import Any

from modules import JWT_HASH_KEY, datetime, jwt, timedelta


def decode_jwt_token(client_token):
    try:
        data = jwt.decode(jwt=client_token, key=JWT_HASH_KEY, algorithms="HS256")
        return data
    except jwt.ExpiredSignatureError as e:
        raise jwt.ExpiredSignatureError(e)


def generate_jwt_token(user_data: dict[str, Any], expire_in_minute: int):
    current_time = datetime.now() + timedelta(minutes=expire_in_minute)
    unix_timestamp = current_time.timestamp()  # expiry time

    payload = {"data": user_data, "exp": int(unix_timestamp)}

    token = jwt.encode(payload, JWT_HASH_KEY, algorithm="HS256")
    return token
