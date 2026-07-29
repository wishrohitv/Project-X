from app import run_app
from utils.extensions import socketio

app = run_app()

if __name__ == "__main__":
    socketio.run(app)
