
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

## API Endpoints

The API is versioned under `/api/v1`. The endpoint permissions are defined in [config/endpoints_permission.py](config/endpoints_permission.py), and all routes are registered by [app.py](app.py).

### Authentication

- `POST /api/v1/auth/signup` — Create an account.
- `POST /api/v1/auth/login` — Log in with a username or email.
- `POST /api/v1/auth/logout` — Log out the current device or all devices with `?all_device=true`.
- `POST /api/v1/auth/refresh` — Refresh an access token. The refresh token is read from the `refresh-token` cookie or `x-refresh-token` header.
- `POST /api/v1/auth/otp/generate` — Generate an OTP for verification.
- `POST /api/v1/auth/otp/verify` — Verify an OTP.
- `GET /api/v1/auth/c/user` — Return the current authenticated user.

### Users and profiles

- `GET /api/v1/users/<string:username>` — Get a public user profile. Optional query parameters: `user_id`, `email_id`.
- `GET /api/v1/users/<string:username>/avatar` — Get a user's avatar URL.
- `PUT /api/v1/users` — Update the current user's name, bio, country, or age.
- `DELETE /api/v1/users` — Delete the current user account (handler is currently not implemented).
- `PUT /api/v1/users/profile_img` — Update the profile image using multipart field `file`.
- `POST /api/v1/users/profile/image` — Upload a profile image.
- `GET /api/v1/users/profile/image` — Get the current profile image.
- `PUT /api/v1/users/profile/image` — Replace the current profile image.
- `DELETE /api/v1/users/profile/image` — Delete the current profile image.
- `POST /api/v1/users/<int:user_id>/follow` — Follow a user.
- `DELETE /api/v1/users/<int:user_id>/follow` — Unfollow a user.
- `GET /api/v1/users/<int:user_id>/followers` — List followers. Supports `limit` and `offset`.
- `GET /api/v1/users/<int:user_id>/followings` — List followed users. Supports `limit` and `offset`.
- `POST /api/v1/users/<int:user_id>/block` — Block a user.
- `DELETE /api/v1/users/<int:user_id>/block` — Unblock a user.
- `GET /api/v1/users/<int:user_id>/blocked` — List blocked users. Supports `limit` and `offset`.
- `POST /api/v1/users/<int:user_id>/report` — Report a user with a JSON `reason`.
- `PUT /api/v1/users/<int:report_id>/report-inspector` — Inspect a user report (moderator/admin).
- `POST /api/v1/users/<int:user_id>/suspend` — Suspend a user (moderator/admin).
- `POST /api/v1/users/<int:user_id>/ban` — Ban a user (admin).
- `PUT /api/v1/users/<int:user_id>/ban` — Unban a user (admin).

### Feeds

- `GET /api/v1/feed` — Get the home feed. Supports `offset`, `limit`, `category`, and `template=true|false`.
- `GET /api/v1/feed/followings` — Get posts from followed users. Supports `offset` and `limit`.

### Posts

- `GET /api/v1/posts/<string:username>` — List a user's posts. Supports `order_by=latest|popular`, `category`, `limit`, and `offset`.
- `GET /api/v1/posts/<string:username>/replies` — List a user's replies. Supports `order_by`, `limit`, and `offset`.
- `GET /api/v1/posts/<string:username>/bookmarked` — List a user's bookmarked posts. Supports `order_by`, `limit`, and `offset`.
- `GET /api/v1/posts/<string:username>/liked` — List a user's liked posts. Supports `order_by`, `limit`, and `offset`.
- `GET /api/v1/posts/<string:username>/templates` — List a user's meme templates. Supports `order_by`, `limit`, and `offset`.
- `GET /api/v1/posts/<int:post_id>` — Get a post by ID.
- `GET /api/v1/posts/<int:post_id>/replies` — List replies to a post.
- `GET /api/v1/posts/<int:post_id>/liked-users` — List users who liked a post.
- `GET /api/v1/posts/<int:post_id>/bookmarked-users` — List users who bookmarked a post.
- `GET /api/v1/posts/<int:post_id>/reposted-users` — List users who reposted a post.
- `GET /api/v1/posts/<int:post_id>/qouted-users` — List users who quoted a post. The `qouted` spelling is part of the current API path.
- `POST /api/v1/posts` — Create a post, reply, or media post. Text is sent as `post_title`; media uses multipart field `files`. Replies use `is_reply=true` and `parent_post_id`.
- `PATCH /api/v1/posts/<int:post_id>` — Update a post.
- `DELETE /api/v1/posts/<int:post_id>` — Delete a post.
- `POST /api/v1/posts/<int:post_id>/repost` — Repost a post.
- `DELETE /api/v1/posts/<int:post_id>/repost` — Undo a repost.
- `POST /api/v1/posts/<int:post_id>/like` — Like a post.
- `DELETE /api/v1/posts/<int:post_id>/like` — Remove a like.
- `POST /api/v1/posts/<int:post_id>/bookmark` — Bookmark a post.
- `DELETE /api/v1/posts/<int:post_id>/bookmark` — Remove a bookmark.
- `POST /api/v1/posts/<int:post_id>/template` — Mark a post as a meme template.
- `DELETE /api/v1/posts/<int:post_id>/template` — Unmark a meme template.
- `POST /api/v1/posts/<int:post_id>/report` — Report a post.
- `POST /api/v1/posts/<int:post_id>/report-inspector` — Inspect a post report (moderator/admin).

### Collections

- `GET /api/v1/collections/list/<int:user_id>` — List a user's collections.
- `GET /api/v1/collections/<int:collection_id>` — Get a collection.
- `POST /api/v1/collections` — Create a collection with JSON `name` and optional `description`.
- `PATCH /api/v1/collections/<int:collection_id>` — Update a collection.
- `DELETE /api/v1/collections/<int:collection_id>` — Delete a collection.
- `POST /api/v1/collections/<int:collection_id>/<int:post_id>` — Add a post to a collection.
- `DELETE /api/v1/collections/<int:collection_id>/<int:post_id>` — Remove a post from a collection.

### Notifications

- `GET /api/v1/notifications` — List notifications. Supports `mention`, `limit`, and `offset`.
- `GET /api/v1/notifications/unread-count` — Get the unread notification count.
- `PATCH /api/v1/notifications/<int:notification_id>/clicked` — Mark a notification as clicked.

### Search and trending

- `GET /api/v1/search` — Search users and posts. Required query parameter: `q`. Optional `filter_by=people|post|all`, `limit`, and `offset`.
- `GET /api/v1/search/suggestion` — Get search suggestions. Required query parameter: `q`.
- `GET /api/v1/trending` — Get trending hashtags.
- `GET /api/v1/trending/<string:hash_tag>/post` — Get posts for a hashtag. Supports `limit` and `offset`.

### Media and asset delivery

- `GET /api/v1/get_post_media/<int:post_id>` — Download the media attached to a post.
- `GET /api/v1/post_media/<path:filename>` — Serve a stored post asset.
- `GET /api/v1/get_profile_image/<string:username>` — Return a profile image URL.
- `GET /api/v1/user_profile/<path:filename>` — Serve a stored profile image.

### API conventions and recent behavior

- Authenticated routes require the access token in the `Authorization` header. Routes marked as partially accessible may also be called without authentication.
- List endpoints generally use `limit` and `offset`; feed and user-list endpoints reject invalid limits, and search/trending endpoints cap pagination at 10.
- Post and feed responses now expose `parent_post_id` for non-reply posts with a parent relationship; reply posts return `null` for this field.
- User profile responses include the user's total post count, and a user's posts view excludes replies.
- Errors are returned as JSON with `code`, `error`, and `description` fields.

Refer to the route handlers under [routes/v1](routes/v1) and the permission registry under [config/endpoints_permission.py](config/endpoints_permission.py) for exact request and response details.

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


