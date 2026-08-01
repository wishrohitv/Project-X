# Project X

Project X is a social media platform for sharing and discovering posts. Users can create profiles, upload their own posts, follow other users, and engage with the community through likes, comments, and reposts and can create collections of posts.


### Server hosted on a VPS

  Visit the [vps.memer.in](https://vps.memer.in/api/v1/feed) to see, use the project in action.

A project for social media for sharing posts

## Core Highlights

- **AI Agent:** `NARA` is an AI assistant/bot integrated into the app, similar to Grok.
- **WebSockets Notifications:** Real-time notification delivery powered by Flask-SocketIO.
- **JWT Authentication:** Secure session and auth flows using JWT tokens for access and refresh.
- **Role-Based Access Control:** Strong RBAC system governing endpoint permissions and user roles.
- **Redis & Caching:** Redis is used for caching, for ratelimiting.
- **Background Workers & Queues:** Python’s built-in queue mechanism is used to process asynchronous tasks such as notifications, emails, and other background jobs.
- **Rate Limiting:** Request throttling is enforced across key API endpoints.


## Features

- User Authentication
- Meme Templates
- User Profiles
- User Uploads
- User Followers
- User Mentions
- Block User
- Report User
- Like Post
- Reply/Comments System (Nested like Twitter)
- Repost Post
- Bookmark Post
- Share Post
- Not interested in Post
- Report Post
- Post Privacy (Public, Private)
- Post likes, bookmarks and download count
- Collections (User can create, edit, delete and share collections of memes like Youtube playlist)
- Search Functionality
- Notifications (Real-time notifications for likes, comments, and new posts) using WebSockets
- **NARA** (AI agent bot similar to Grok bot)
- Analytics (Planned - not implemented yet)
- Chat (Planned - not implemented yet)


<!--## Tech Stack
- Frontend: Html, Tailwind CSS, Vanilla JS
- Backend: Python, Flask, SQLAlchemy, Flask-CORS, Redis, Resend, Cloudinary
- Database: PostgreSQL
- Deployment: Vercel (Frontend, Backend)-->

## System Architecture
### Backend
- Built with Python and Flask
- Uses SQLAlchemy for database ORM
- Utilizes Flask-CORS for cross-origin resource sharing
- Redis for caching and session management
- Resend for email delivery
- Cloudinary for media management

### Frontend
- Built with HTML, Tailwind CSS, and Vanilla JS
- SPA architecture 


## Third-Party Services
- Resend is used for sending transactional emails such as account verification, password reset, and notifications to users. It provides a reliable and scalable email delivery service with features like email templates, analytics, and support for various email protocols.
- Cloudinary is used for storing and managing media assets such as meme images uploaded by users. It offers a cloud-based media management solution with features like image optimization, transformation, and delivery through a global content delivery network (CDN).
- Redis is used for caching and session management in the backend. It provides a fast and efficient in-memory data store that can be used to cache frequently accessed data, manage user sessions, and improve the overall performance of the application.


## Installation
See `docs/setup.md` for installation steps, `.env` setup, and backend configuration mapping.

## Backend

For full backend details, architecture overview, endpoint descriptions, and deployment notes, see [backend/README.md](backend/README.md).
