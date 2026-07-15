# App name
APP_NAME: str = "Project X"

# App version
APP_VERSION: str = "1.0.0"

# Media storage
USE_CLOUDINARY_STORAGE: bool = False  # If true then cloudinary service will be used for storing user uploaded media file, else local computer storage will be used to store media files

USE_EMAIL_SERVICE: bool = False  # If true then email service will be used for sending OTP, else email service will be used to send OTP (RESEND_API_KEY)

USE_REDIS: bool = False  # If true then redis service will be used for caching, else local memory will be used for caching

USE_BOT_SERVICE: bool = True  # If true then bot service will be used for generating responses by [@botuser], else default behavior will be used

# Background task thread
BACKGROUND_TASK_NUMBER_OF_THREADS: int = (
    3  # Number of worker threads for background task processing
)

USER_ACCOUNT_STATUS: list[str] = ["active", "suspended", "banned", "deleted"]

SEREVR_ALLOWED_UPLOAD_FILE_SIZE: int = 20 * 1024 * 1024  # 20 MB
ALLOWED_IMG_FILE_SIZE: int = 5 * 1024 * 1024  # 5 MB
ALLOWED_VID_FILE_SIZE: int = SEREVR_ALLOWED_UPLOAD_FILE_SIZE  # 20 MB

# Allowed file size for posts
ALLOWED_POST_FILE_SIZE: dict[str, int] = {
    "image/jpeg": ALLOWED_IMG_FILE_SIZE,
    "image/png": ALLOWED_IMG_FILE_SIZE,
    "image/webp": ALLOWED_IMG_FILE_SIZE,
    "video/mp4": ALLOWED_VID_FILE_SIZE,
    "image/gif": ALLOWED_IMG_FILE_SIZE,
}

ALLOWED_PROFILE_FILE_MIMETYPE: dict[str, str] = {
    # mimeType : extension
    "image/jpeg": "jpeg",
    "image/png": "png",
    "image/webp": "webp",
    "image/gif": "gif",
}
ALLOWED_PROFILE_FILE_SIZE: dict[str, int] = {
    "image/jpeg": 2 * 1024 * 1024,  # 2 MB
    "image/png": 2 * 1024 * 1024,  # 2 MB
    "image/webp": 2 * 1024 * 1024,  # 2 MB
    "image/gif": 2 * 1024 * 1024,  # 2 MB
}

# Allowed file size for user profile
ALLOWED_POST_FILE_MIMETYPE: dict[str, str] = {
    # mimeType : extension
    "image/jpeg": "jpeg",
    "image/png": "png",
    "image/webp": "webp",
    "video/mp4": "mp4",
    "image/gif": "gif",
}

# Public directory to store clients media data
PUBLIC_DIRECTORY_PROFILES: str = "public/profiles"
PUBLIC_DIRECTORY_POSTS: str = "public/posts"

API_ROOT_URL: str | None = None  # Domain name

LOGGING_PATH: str = "logs"

ACCESS_TOKEN_EXPIRY_MINUTES: int = 30  # Minute

REFRESH_TOKEN_EXPIRY_MINUTES: int = 60 * 24 * 10  # 10 days

SECURE_COOKIE: bool = True  # Set always true

HTTP_ONLY: bool = True  # Set always true
