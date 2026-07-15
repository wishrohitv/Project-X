# Project X

Project X is a social media platform for sharing and discovering posts. Users can create profiles, upload their own posts, follow other users, and engage with the community through likes, comments, and reposts and can create collections of posts.


### Frontend Status
-- Work in Progress
  Visit the [memer.in](https://memer.in) to see, use the project in action.

A project for social media for sharing posts
contains frontend and backend

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
- **NARA** (AI chat bot similar to Grok bot) underlying AI Agent
- Analytics (Planned - not implemented yet)
- Chat (Planned - not implemented yet)

## Tech Stack
- Frontend: Html, Tailwind CSS, Vanilla JS
- Backend: Python, Flask, SQLAlchemy, Flask-CORS, Redis, Resend, Cloudinary
- Database: PostgreSQL
- Deployment: Vercel (Frontend, Backend)

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
 Go to [Docs](./docs/setup.md) folder and follow the instructions in the setup.md file to set up the project locally.
