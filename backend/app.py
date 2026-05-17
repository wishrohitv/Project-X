from database import initialize_db
from dotenv import load_dotenv
from modules import (
    CORS,
    HOST,
    PORT,
    SEREVR_ALLOWED_UPLOAD_FILE_SIZE,
    Flask,
    jsonify,
    os,
    traceback,
)
from repository.init_db_setup import init_db_setup
from tasks import start_worker
from utils import AppError

load_dotenv()


def run_app():
    # Initialize database
    initialize_db()

    app = Flask(__name__)
    app.secret_key = os.environ.get("APP_SECRET_KEY") or "default_secret_key"
    origins = os.environ.get("ORIGINS")
    CORS(
        app,
        supports_credentials=True,
        origins=origins.split(",") if origins else ["*"],
    )

    app.config["path"] = "backend/public"
    app.config["MAX_CONTENT_LENGTH"] = SEREVR_ALLOWED_UPLOAD_FILE_SIZE

    # Blueprint for auth
    from routes.v1.auth import auth_blueprint

    # Blueprint for post collection of posts
    from routes.v1.collections import (
        collection_blueprint,
    )

    # Register Bluprint for homeFeed endpoint
    from routes.v1.feed import feed_blueprint

    # Blueprint for notifications
    from routes.v1.notifications import notification_blueprint

    # Blueprint for posts
    from routes.v1.posts import posts_blueprint

    # Blueprint for posts, profile media content of user
    from routes.v1.return_media_asset import return_media_assets_blueprint

    # Blueprint for user profile data
    from routes.v1.users import users_blueprint

    app.register_blueprint(auth_blueprint, url_prefix="/api/v1")
    app.register_blueprint(return_media_assets_blueprint, url_prefix="/api/v1")
    app.register_blueprint(posts_blueprint, url_prefix="/api/v1")
    app.register_blueprint(users_blueprint, url_prefix="/api/v1")
    app.register_blueprint(feed_blueprint, url_prefix="/api/v1")
    app.register_blueprint(collection_blueprint, url_prefix="/api/v1")
    app.register_blueprint(notification_blueprint, url_prefix="/api/v1")

    # Register handler for the custom exception

    @app.errorhandler(AppError)
    def handle_custom_error(error: AppError):
        if error.code >= 500:
            traceback.print_exception(
                type(error),
                error,
                error.__traceback__,
            )

        # Log the error, return a custom JSON response or render a custom template
        return jsonify(
            {"code": error.code, "error": error.error, "description": error.description}
        ), error.code

    # init_db_setup
    init_db_setup()
    # Start background worker
    start_worker()

    return app


if __name__ == "__main__":
    app = run_app()
    app.run(debug=True, host=HOST, port=PORT)
