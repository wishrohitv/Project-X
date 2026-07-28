
# Memestore — Backend

This directory contains the backend for Project Memestore — a lightweight social-sharing service for posts and meme templates. The backend is built with Flask, SQLAlchemy and provides REST APIs, background tasks, and real-time notifications.

## Quick Overview

- **Language:** Python 3.9+
- **Framework:** Flask
- **Database:** PostgreSQL (SQLAlchemy)
- **Cache / Real-time:** Redis
- **Migrations:** Alembic
- **Realtime:** Flask-SocketIO

## Key Features

- JWT-based authentication and authorization
- CRUD for posts, collections, profiles
- Real-time notifications and socket events
- Media uploads and delivery (Cloudinary integration)
- Background tasks for async jobs
- Search and feed generation logic

## Tech Stack

- Flask, Flask-SocketIO
- SQLAlchemy ORM
- Alembic for migrations
- Redis for caching and pub/sub
- Cloudinary for media storage
- Resend (email) and Google Gemini (AI integrations)

## Project Layout

Top-level files you will use frequently:

- [app.py](app.py) — application entrypoint and server startup
- [database.py](database.py) — DB initialization and helpers
- [settings.py](settings.py) — configuration helper reading env vars
- [requirements.txt](requirements.txt) — Python dependencies
- [routes/v1](routes/v1) — REST API endpoints (versioned)
- [repository](repository) — DB access logic
- [services](services) — external integrations and business logic
- [models](models) — SQLAlchemy models

## Quickstart (Development)

1. Create and activate a Python virtualenv:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Create a `.env` file in this `backend/` directory. Minimum required vars:

```env
PORT=5000
HOST=0.0.0.0
DEBUG=True
APP_SECRET_KEY=replace_me
DB_URL=postgresql://user:pass@localhost:5432/memestore
JWT_HASH_KEY=replace_me
REDIS_URL=redis://localhost:6379/0
CLOUDINARY_URL=cloudinary://<key>:<secret>@<cloud_name>
RESEND_API_KEY=replace_me
GEMINI_API_KEY=replace_me
GEMINI_MODEL_NAME=replace_me
ORIGINS=http://localhost:3000
```

4. Initialize the database (creates tables defined by models):

```bash
python -c "from database import initialize_db; initialize_db()"
```

5. Run pending migrations (if any):

```bash
alembic upgrade head
```

6. Start the dev server:

```bash
python app.py
```

The app will start on the port configured in `.env` (default `5000`).

## Running in Production

Use a WSGI server (Gunicorn) with an appropriate worker class for WebSocket support:

```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:run_app() --worker-class geventwebsocket.gunicorn.workers.GeventWebSocketWorker
```

Adjust worker count and resource limits for your deployment.

## Database & Migrations

- Models live under the [models](models) package.
- Use Alembic to generate and apply migrations:

```bash
alembic revision --autogenerate -m "Describe change"
alembic upgrade head
```

If you need to recreate the DB schema during development, use `initialize_db()` in `database.py`.

## API Endpoints (overview)

All endpoints are prefixed with `/api/v1`.

- `POST /api/v1/auth/register` — register a user
- `POST /api/v1/auth/login` — login and receive access token
- `GET /api/v1/posts` — list posts
- `POST /api/v1/posts` — create a post
- `GET /api/v1/users/:id` — get user profile
- `GET /api/v1/feed` — user feed
- `GET /api/v1/search` — search posts/users

Refer to the route handlers under [routes/v1](routes/v1) for the exact request/response formats and query parameters.

## Real-time Notifications

The app exposes SocketIO events (namespace `/notifications`). See [services/socket_service.py](services/socket_service.py) for server-side event handling and emit patterns.

## Development Tips

- Keep `.env` out of version control; use environment-specific configs for deployments.
- Use Redis locally to test realtime features and background tasks.
- Write small, focused migrations; use `--autogenerate` as a starting point and review diffs.

## Tests

There are lightweight tests under the `tests/` folder. Run them with your preferred test runner (e.g., `pytest`).

## Contributing

See [improvements.md](improvements.md) for potential contributor tasks and ideas. When opening PRs, include a short description, testing notes, and migration steps if DB changes are included.

## License

TBD — add your preferred license file at the repo root (e.g., `LICENSE`).

---

If you'd like, I can also:

- Expand the API section with full request/response examples.
- Create a root-level `README.md` summarizing the whole Project-MemeStore.
- Add a simple Postman/HTTPie collection for quick API testing.

