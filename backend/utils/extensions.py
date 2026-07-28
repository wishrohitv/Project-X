from modules import SocketIO
from settings import Settings

socketio = SocketIO(cors_allowed_origins=Settings.ORIGINS.split(",") or "*")
