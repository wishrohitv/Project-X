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

    # # Blueprint for auth
    # from routes.v1.auth import authBlueprint

    # # Blueprint for post collection of posts
    # from routes.v1.collections import (
    #     collectionBlueprint,
    # )

    # # Register Bluprint for homeFeed endpoint
    # from routes.v1.feed import feedBlueprint

    # # Blueprint for notifications
    # from routes.v1.notifications import notificationBlueprint

    # # Blueprint for posts
    # from routes.v1.posts import postsBlueprint

    # # Blueprint for posts media content of user
    # from routes.v1.returnPostMedia import getPostMediaRouteBlueprint

    # # Blueprint for profile image fetch of user
    # from routes.v1.returnProfileImage import (
    #     getProfileImageRouteBlueprint,
    # )

    # Blueprint for user profile data
    from routes.v1.users import users_blueprint

    # app.register_blueprint(authBlueprint, url_prefix="/api/v1")
    # app.register_blueprint(getProfileImageRouteBlueprint, url_prefix="/api/v1")
    # app.register_blueprint(getPostMediaRouteBlueprint, url_prefix="/api/v1")
    # app.register_blueprint(postsBlueprint, url_prefix="/api/v1")
    app.register_blueprint(users_blueprint, url_prefix="/api/v1")
    # app.register_blueprint(feedBlueprint, url_prefix="/api/v1")
    # app.register_blueprint(collectionBlueprint, url_prefix="/api/v1")
    # app.register_blueprint(notificationBlueprint, url_prefix="/api/v1")

    # Register handler for the custom exception

    @app.errorhandler(AppError)
    def handle_custom_error(error: AppError):
        traceback.print_exc()
        (getattr(error, "code", 500),)
        # Log the error, return a custom JSON response or render a custom template
        response = (
            jsonify(
                {
                    "code": error.code,
                    "error": error.error,
                    "description": error.description,
                }
            ),
        )
        response.status_code = error.code or 500
        return response

    # init_db_setup
    init_db_setup()
    # Start background worker
    start_worker()

    return app


if __name__ == "__main__":
    app = run_app()
    app.run(debug=True, host=HOST, port=PORT)
