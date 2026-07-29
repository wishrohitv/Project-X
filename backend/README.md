
# Project-X — Backend

This directory contains the backend for Project Project-X — a lightweight social-sharing service for posts and meme templates. The backend is built with Flask, SQLAlchemy and provides REST APIs, background tasks, and real-time notifications.

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

## Backend folder structure

- `backend/`
  - `.env` — environment file for runtime configuration
  - `alembic.ini` — Alembic configuration
  - `app.py` — app creation and startup logic
  - `wsgi.py` — WSGI entrypoint for production servers
  - `database.py` — database initialization
  - `config/` — permission and role configuration
  - `routes/` — request routing and endpoint handlers
  - `models/` — SQLAlchemy model definitions
  - `repository/` — database access layer
  - `services/` — external integrations and business logic
  - `tasks/` — background worker and task interfaces
  - `utils/` — helpers, error handling, logging, extensions
  - `public/` — static media assets
  - `logs/` — runtime logs

## Running in Production

Use a WSGI server (Gunicorn) with a gevent worker for WebSocket support:

```bash
gunicorn -w 4 -b 0.0.0.0:5000 -k gevent wsgi:app 
```

Adjust worker count and resource limits for your deployment.

If you need to recreate the DB schema during development, use `initialize_db()` in `database.py`.

## API Endpoints (overview)

All endpoints are prefixed with `/api/v1`.

### Auth
- `POST /api/v1/auth/signup`
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/logout`
- `POST /api/v1/auth/refresh`
- `POST /api/v1/auth/otp/generate`
- `POST /api/v1/auth/otp/verify`
- `GET /api/v1/auth/c/user`

### Users
- `GET /api/v1/users/<string:username>`
- `DELETE /api/v1/users`
- `PUT /api/v1/users`
- `PUT /api/v1/users/profile_img`
- `POST /api/v1/users/profile/image`
- `GET /api/v1/users/profile/image`
- `PUT /api/v1/users/profile/image`
- `DELETE /api/v1/users/profile/image`
- `POST /api/v1/users/<int:user_id>/follow`
- `DELETE /api/v1/users/<int:user_id>/follow`
- `GET /api/v1/users/<int:user_id>/followers`
- `GET /api/v1/users/<int:user_id>/followings`
- `GET /api/v1/users/<int:user_id>/blocked`
- `POST /api/v1/users/<int:user_id>/block`
- `DELETE /api/v1/users/<int:user_id>/block`
- `POST /api/v1/users/<int:user_id>/report`
- `PUT /api/v1/users/<int:report_id>/report-inspector`
- `POST /api/v1/users/<int:user_id>/suspend`

### Feed
- `GET /api/v1/feed`

### Posts
- `GET /api/v1/posts/<string:username>`
- `GET /api/v1/posts/<int:post_id>`
- `GET /api/v1/posts/<int:post_id>/liked-users`
- `GET /api/v1/posts/<int:post_id>/bookmarked-users`
- `GET /api/v1/posts/<int:post_id>/reposted-users`
- `GET /api/v1/posts/<int:post_id>/qouted-users`
- `POST /api/v1/posts`
- `POST /api/v1/posts/<int:post_id>/repost`
- `DELETE /api/v1/posts/<int:post_id>/repost`
- `POST /api/v1/posts/<int:post_id>/like`
- `DELETE /api/v1/posts/<int:post_id>/like`
- `POST /api/v1/posts/<int:post_id>/bookmark`
- `DELETE /api/v1/posts/<int:post_id>/bookmark`
- `DELETE /api/v1/posts/<int:post_id>`
- `PATCH /api/v1/posts/<int:post_id>`
- `POST /api/v1/posts/<int:post_id>/report`
- `POST /api/v1/posts/<int:post_id>/report-inspector`
- `GET /api/v1/posts/<int:post_id>/replies`
- `POST /api/v1/posts/<int:post_id>/template`
- `DELETE /api/v1/posts/<int:post_id>/template`

### Collections
- `GET /api/v1/collections/list/<int:user_id>`
- `GET /api/v1/collections/<int:collection_id>`
- `POST /api/v1/collections`
- `DELETE /api/v1/collections/<int:collection_id>`
- `PATCH /api/v1/collections/<int:collection_id>`
- `POST /api/v1/collections/<int:collection_id>/<int:post_id>`
- `DELETE /api/v1/collections/<int:collection_id>/<int:post_id>`

### Notifications
- `GET /api/v1/notifications`
- `GET /api/v1/notifications/unread-count`
- `PATCH /api/v1/notifications/<int:notification_id>/clicked`

### Search
- `GET /api/v1/search`
- `GET /api/v1/search/suggestion`
- `GET /api/v1/trending`
- `GET /api/v1/trending/<string:hash_tag>/post`

### Media / asset delivery
- `GET /api/v1/get_post_media/<int:post_id>`
- `GET /api/v1/post_media/<path:filename>`
- `GET /api/v1/get_profile_image/<string:username>`
- `GET /api/v1/user_profile/<path:filename>`

Refer to the route handlers under [routes/v1](routes/v1) for exact request and response details.

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

