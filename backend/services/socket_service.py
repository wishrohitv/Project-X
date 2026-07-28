from modules import Namespace, emit, join_room, jwt, request, rooms
from utils import Logging, decode_jwt_token
from utils.extensions import socketio

Log = Logging(__name__)


class NotificationServer(Namespace):
    def __init__(self, namespace="/notifications"):
        super().__init__(namespace)

    # Default connect handler
    def on_auth_connect(self, auth: dict[str, str]):
        Log.info("Client connection attempt detected")

        access_token = auth.get("access_token")

        if not access_token:
            Log.warning("Connection rejected: No auth token provided")
            return False

        decoded_token = None

        try:
            decoded_token = decode_jwt_token(access_token)
        except jwt.ExpiredSignatureError:
            Log.warning("User token expired")
            return False
        except Exception as _:
            Log.warning("Invalid token structure")
            return False


        if decoded_token:
            user_id = decoded_token["payload"]["id"]
            join_room(user_id)
            emit("on_connect", {"success": True})
            Log.info(f"Client connected successfully. User ID: {user_id}")
        else:
            return False

    def on_disconnect(self):
        Log.info("Client disconnected")
        emit("on_disconnect", "Client disconnected")
