# Setup guide

## Install backend dependencies

1. Open a terminal in the repository root.
2. Create and activate a Python virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

3. Install backend dependencies:

```bash
pip install -r backend/requirements.txt
```

## Create `.env`

Create a file at `backend/.env` and add the following environment variables. These values are loaded automatically by `backend/settings.py` via `python-dotenv`.

```bash
HOST=0.0.0.0
PORT=5000
DEBUG=True
ORIGINS=http://127.0.0.1:8000
APP_SECRET_KEY=your_secret_key
DB_URL=postgresql://username:password@localhost:5432/memestore
REDIS_URL=redis://localhost:6379
CLOUDINARY_URL=cloudinary://api_key:api_secret@cloud_name
RESEND_API_KEY=your_resend_api_key
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL_NAME=gpt-4o-mini
API_ROOT_URL=http://localhost:5000
JWT_ACCESS_TOKEN_HASH_KEY=your_access_hash_key
JWT_REFRESH_TOKEN_HASH_KEY=your_refresh_hash_key
ACCESS_TOKEN_EXPIRY_MINUTES=30
REFRESH_TOKEN_EXPIRY_MINUTES=14400
SECURE_COOKIE=True
HTTP_ONLY=True
```

### Notes

- `APP_SECRET_KEY` is used for signing tokens and session secrets. If omitted, the app will generate a temporary key at startup.
- `DB_URL, REDIS_URL`, and `RESEND_API_KEY` are required to connect to PostgreSQL, Redis, and Resend.
- `CLOUDINARY_URL` is optional depending on whether you use Cloudinary features.
- `ORIGINS` should match the frontend or client origins you allow for CORS.

## Environment variables mapped to `backend/settings.py`

The following variables are read from `backend/.env` and mapped into the `Settings` class in `backend/settings.py`:

- `HOST` → `Settings.HOST`
- `PORT` → `Settings.PORT`
- `DEBUG` → `Settings.DEBUG`
- `ORIGINS` → `Settings.ORIGINS`
- `APP_SECRET_KEY` → `Settings.APP_SECRET_KEY`
- `DB_URL` → `Settings.DB_URL`
- `GEMINI_API_KEY` → `Settings.GEMINI_API_KEY`
- `GEMINI_MODEL_NAME` → `Settings.GEMINI_MODEL_NAME`
- `REDIS_URL` → `Settings.REDIS_URL`
- `RESEND_API_KEY` → `Settings.RESEND_API_KEY`
- `CLOUDINARY_URL` → `Settings.CLOUDINARY_URL`
- `API_ROOT_URL` → `Settings.API_ROOT_URL`
- `JWT_ACCESS_TOKEN_HASH_KEY` → `Settings.JWT_ACCESS_TOKEN_HASH_KEY`
- `JWT_REFRESH_TOKEN_HASH_KEY` → `Settings.JWT_REFRESH_TOKEN_HASH_KEY`
- `ACCESS_TOKEN_EXPIRY_MINUTES` → `Settings.ACCESS_TOKEN_EXPIRY_MINUTES`
- `REFRESH_TOKEN_EXPIRY_MINUTES` → `Settings.REFRESH_TOKEN_EXPIRY_MINUTES`
- `SECURE_COOKIE` → `Settings.SECURE_COOKIE`
- `HTTP_ONLY` → `Settings.HTTP_ONLY`

## Run the backend

From the `backend/` directory, start the app with the normal command for this project, such as:

```bash
python -m app
```

Or use whichever launch command is defined in your backend README.
