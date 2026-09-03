from database import SessionLocal, redis_client
from models import Bookmark, Category, Follower, Likes, Posts, Profile, Reposts, Users
from modules import (
    USE_CLOUDINARY_STORAGE,
    aliased,
    exists,
    func,
    json,
    literal,
    logging,
    request,
    select,
    url_for,
)
from settings import Settings
from utils import (
    AppError,
    BadRequestError,
    InternalServerError,
    SuccessResponse,
    fname,
)

Log = logging.getLogger(__name__)


def _get_home_feed(
    category: list = [],
    offset: int = 0,
    limit: int = 10,
    fetch_template: bool = False,
    session_user_id: int | None = None,
):
    session = SessionLocal()

    redis_key = f"home_feed:{offset}:{limit}"
    cached_feed = redis_client.get(redis_key)
    if cached_feed:
        Log.info("Redis hit: returning cached home feed")

        return SuccessResponse(
            data=json.loads(cached_feed),
            message="Home feed fetched successfully",
            status_code=200,
        )

    try:
        # Fetch only public posts and isReply false
        conditions = [
            Posts.visibility,
            Posts.is_reply.is_(False),
            Posts.is_deleted.is_(False),
        ]
        if fetch_template:
            conditions.append(Posts.is_template.is_(True))
        feed = _query_posts(conditions, category, offset, limit, session_user_id)

        Log.info("Redis miss: fetching home feed from database")
        redis_client.set(redis_key, json.dumps(feed), ex=100)
        return SuccessResponse(
            data=feed, message="Home feed fetched successfully", status_code=200
        )
    except AppError:
        raise
    except Exception as e:
        raise InternalServerError("Error while fetching home feed") from e
    finally:
        session.close()


def _get_home_feed_followings(
    session_user_id: int,
    offset: int = 0,
    limit: int = 10,
):
    session = SessionLocal()

    redis_key = f"home_feed_followings:{session_user_id}:{offset}:{limit}"
    cached_feed = redis_client.get(redis_key)
    if cached_feed:
        Log.info("Redis hit: returning cached home feed")
        return SuccessResponse(
            data=json.loads(cached_feed),
            message="Home feed fetched successfully",
            status_code=200,
        )

    try:
        # Fetch only public posts and isReply false
        conditions = [
            Posts.visibility,
            Posts.is_reply.is_(False),
            Posts.is_deleted.is_(False),
            Follower.follower_id == session_user_id,
        ]
        join_model = Follower
        join_conditions = Follower.user_id == Users.id

        feed = _query_posts(
            conditions=conditions,
            category=[],
            offset=offset,
            limit=limit,
            session_user_id=session_user_id,
            join_model=join_model,
            join_conditions=join_conditions,
        )

        Log.info("Redis miss: fetching home feed from database")
        redis_client.set(redis_key, json.dumps(feed), ex=100)
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
    order_by: str = "latest",
    join_model=None,
    join_conditions=None,
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
                ).label("is_liked")
                if session_user_id
                else literal(False).label("is_liked"),
                exists(
                    select(Bookmark).where(
                        Bookmark.post_id == Posts.id,
                        Bookmark.user_id == session_user_id,
                    )
                ).label("is_bookmarked")
                if session_user_id
                else literal(False).label("is_bookmarked"),
                exists(
                    select(Reposts).where(
                        Reposts.post_id == Posts.id, Reposts.user_id == session_user_id
                    )
                ).label("is_reposted")
                if session_user_id
                else literal(False).label("is_reposted"),
            )
            .join_from(Users, Posts)
            .join_from(Users, Profile)
        )

        if join_model:
            stmt = stmt.join_from(Users, join_model, join_conditions).where(*conditions)
        else:
            stmt = stmt.where(*conditions)

        stmt = (
            stmt.limit(limit)
            .offset(offset)
            .order_by(
                Posts.created_at.desc()
                if order_by == "latest"
                else Posts.created_at.asc()
            )
        )

        get_feed = session.execute(stmt).all()

        feed_obj = [
            {
                "user": {
                    "profile_img_url": feed[2]
                    if USE_CLOUDINARY_STORAGE
                    else f"{Settings.API_ROOT_URL or (request.host_url)[:-1]}{url_for('return_assets.serve_image', filename=fname(feed[3], feed[4]))}",
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
                    else f"{Settings.API_ROOT_URL or (request.host_url)[:-1]}{url_for('return_assets.serve_post_media', filename=fname(feed[1].media_public_id, feed[1].file_extension, post=True))}",
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

            if post.user_id == session_user_id:
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
            return {"status": 204, "message": "No posts found"}

        post = {
            "user": {
                "username": result[0],
                "user_id": result[1].user_id,
                "profile_img_url": result[2]
                if USE_CLOUDINARY_STORAGE
                else f"{Settings.API_ROOT_URL or (request.host_url)[:-1]}{url_for('return_assets.serve_image', filename=fname(result[3], result[4]))}",
            },
            "post": {
                "post_id": result[1].id,
                "title": result[1].text,
                "file_type": result[1].file_type,
                "file_extension": result[1].file_extension,
                "created_at": result[1].created_at.isoformat(),
                "age_rating": result[
                    1
                ].age_rating.value,  # Return Enum class from db and get its value from
                "post_media_url": result[1].media_url
                if USE_CLOUDINARY_STORAGE
                else f"{Settings.API_ROOT_URL or (request.host_url)[:-1]}{url_for('return_assets.serve_post_media', filename=fname(result[1].media_public_id, result[1].file_extension, post=True))}",
            },
        }
        return {"status": 200, "data": post}
    except Exception as e:
        return {"status": 500, "error": "Internal Server Error"}
    finally:
        session.close()
