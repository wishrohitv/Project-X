from database import SessionLocal
from models import Bookmark, Category, Likes, Posts, Profile, Reposts, Users
from modules import (
    API_ROOT_URL,
    USE_CLOUDINARY_STORAGE,
    aliased,
    exists,
    func,
    json,
    make_response,
    request,
    select,
    sessionmaker,
    url_for,
)
from utils import AppError, BadRequestError, InternalServerError, SuccessResponse


def _get_home_feed(
    category: list = [],
    offset: int = 0,
    limit: int = 10,
    fetch_template: bool = False,
    session_user_id: int | None = None,
):
    session = SessionLocal()
    try:
        # Fetch only public posts and isReply false
        conditions = [Posts.visibility, Posts.is_reply.is_(False)]
        if fetch_template:
            conditions.append(Posts.is_template.is_(True))
        feed = _query_posts(conditions, category, offset, limit, session_user_id)

        return SuccessResponse(
            data=feed, message="Home feed fetched successfully", status_code=200
        )
    except AppError:
        raise
    except Exception as e:
        raise InternalServerError("Error while fetching home feed") from e
    finally:
        session.close()


def _query_posts(
    conditions,
    category: list[str] = [],
    offset: int = 0,
    limit: int = 10,
    session_user_id: int | None = None,
):
    session = SessionLocal()
    """
    Global feed and post and replie query function
    """
    try:
        # Get feed data from database along with userName of author of post
        like = aliased(Likes)
        like_count = (
            select(func.count(like.user_id))
            .where(like.post_id == Posts.id)
            .correlate(Posts)
            .scalar_subquery()
        )
        repost = aliased(Reposts)
        repost_count = (
            select(func.count(repost.user_id))
            .where(repost.post_id == Posts.id)
            .correlate(Posts)
            .scalar_subquery()
        )
        bookmark = aliased(Bookmark)
        bookmark_count = (
            select(func.count(bookmark.user_id))
            .where(bookmark.post_id == Posts.id)
            .correlate(Posts)
            .scalar_subquery()
        )

        reply = aliased(Posts)
        repliesCount = (
            select(func.count(reply.id))
            .where(reply.parent_post_id == Posts.id, reply.is_reply.is_(True))
            .scalar_subquery()
        )
        stmt = (
            select(
                Users.username,
                Posts,
                Profile.media_url,
                Profile.media_public_id,
                Profile.file_extension,
                like_count.label("like_count"),
                repost_count.label("repost_count"),
                bookmark_count.label("bookmark_count"),
                repliesCount.label("replies_count"),
                exists(
                    select(Likes).where(
                        Likes.post_id == Posts.id, Likes.user_id == session_user_id
                    )
                ).label("is_liked"),
                exists(
                    select(Bookmark).where(
                        Bookmark.post_id == Posts.id,
                        Bookmark.user_id == session_user_id,
                    )
                ).label("is_bookmarked"),
                exists(
                    select(Reposts).where(
                        Reposts.post_id == Posts.id, Reposts.user_id == session_user_id
                    )
                ).label("is_reposted"),
            )
            .join_from(Users, Posts)
            .join_from(Users, Profile)
            .where(*conditions)
            .limit(limit)
            .offset(offset)
        )
        get_feed = session.execute(stmt).all()

        feed_obj = [
            {
                "user": {
                    "profile_img_url": feed[2]
                    if USE_CLOUDINARY_STORAGE
                    else f"{API_ROOT_URL or request.host_url}{url_for('return_assets.serve_image', filename=f'{feed[3]}.{feed[4]}')}",
                    "username": feed[0],
                    "user_id": feed[1].user_id,
                },
                "post": {
                    "post_id": feed[1].id,
                    "text": feed[1].text,
                    "tags": feed[1].tags,
                    "replying_to": feed[1].replying_to,
                    "file_type": feed[1].file_type,
                    "file_extension": feed[1].file_extension,
                    "visibility": feed[1].visibility,
                    "parent_post_id": _get_parent_post(
                        feed[1].parent_post_id, session_user_id
                    )
                    if not feed[1].is_reply
                    else None,  # Check if post's 'is_reply=True' send None because
                    "created_at": feed[1].created_at.isoformat(),
                    "age_rating": feed[
                        1
                    ].age_rating.value,  # Return Enum class from db and get its value from 'age_rating': <PostAgeRating.pg13: 'pg13'>,
                    "category": feed[1].category,
                    "is_template": feed[1].is_template,
                    "post_media_url": feed[1].media_url
                    if USE_CLOUDINARY_STORAGE
                    else f"{API_ROOT_URL or request.host_url}{url_for('return_assets.serve_post_media', filename=f'{feed[1].media_public_id}.{feed[1].file_extension}')}",
                    "like_count": feed[5],
                    "repost_count": feed[6],
                    "bookmark_count": feed[7],
                    "replies_count": feed[8],
                    "is_liked": feed[9],
                    "is_bookmarked": feed[10],
                    "is_reposted": feed[11],
                },
            }
            for feed in get_feed
        ]

        return feed_obj

    except Exception as e:
        raise
    finally:
        session.close()


def _get_parent_post(post_id: int, session_user_id: int | None = None):
    session = SessionLocal()
    try:
        conditions = []
        # Fetch post by ID
        conditions.append(Posts.id == post_id)

        # Check post visibility
        if session_user_id:
            # Check owner of the post
            post = session.query(Posts).where(Posts.id == post_id).first()
            if not post:
                return {"status": 404, "error": "Post not found"}

            if not post.user_id == session_user_id:
                # Check whether post's visibility is true or false
                if not post.visibility:
                    return {"status": 403, "error": "Post is private"}

                # Fetch only public posts
                conditions.append(Posts.visibility)

        stmt = (
            select(
                Users.username,
                Posts,
                Profile.media_url,
                Profile.media_public_id,
                Profile.file_extension,
            )
            .join_from(Users, Posts)
            .join_from(Users, Profile)
            .where(*conditions)
        )

        result = session.execute(stmt).fetchone()
        if not result:
            return {"error": "Post not found"}

        post = {
            "username": result[0],
            "post_id": result[1].id,
            "title": result[1].text,
            "user_id": result[1].user_id,
            "file_type": result[1].file_type,
            "media_public_id": result[1].media_public_id,
            "file_extension": result[1].file_extension,
            "created_at": result[1].created_at.isoformat(),
            "age_rating": result[
                1
            ].age_rating.value,  # Return Enum class from db and get its value from
            "post_media_url": result[1].media_url
            if USE_CLOUDINARY_STORAGE
            else f"{API_ROOT_URL or request.host_url}{url_for('return_assets.serve_post_media', filename=f'{result[1].media_public_id}.{result[1].file_extension}')}",
            "profile_img_url": result[2]
            if USE_CLOUDINARY_STORAGE
            else f"{API_ROOT_URL or request.host_url}{url_for('return_assets.serve_image', filename=f'{result[3]}.{result[4]}')}",
        }
        return {"status": 200, "data": post}
    except Exception as e:
        return {"status": 500, "error": "Internal Server Error"}
    finally:
        session.close()
