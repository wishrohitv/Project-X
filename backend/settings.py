import os
from secrets import token_hex

from dotenv import load_dotenv

load_dotenv()


class Settings:
    PORT: int = int(os.environ.get("PORT", 5000))
    HOST: str = os.environ.get("HOST", "0.0.0.0")
    DEBUG: bool = str(os.environ.get("DEBUG", False)).lower() == "true"

    ORIGINS: str | None = os.environ.get("ORIGINS")
    APP_SECRET_KEY: str = os.environ.get("APP_SECRET_KEY", token_hex(64))
    DB_URL: str | None = os.environ.get("DB_URL")

    JWT_HASH_KEY: str = os.environ.get("JWT_HASH_KEY", "Thisisdefaultkeyforhasing")

    GEMINI_API_KEY: str | None = os.environ.get("GEMINI_API_KEY")
    GEMINI_MODEL_NAME: str | None = os.environ.get("GEMINI_MODEL_NAME")
    REDIS_URL: str = os.environ.get("REDIS_URL", "redis://localhost:6379")
    RESEND_API_KEY: str | None = os.environ.get("RESEND_API_KEY")
    CLOUDINARY_URL: str | None = os.environ.get("CLOUDINARY_URL")
