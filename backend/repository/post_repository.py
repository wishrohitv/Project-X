from database import SessionLocal, redis_client
from models import (
    AgeRating,
    Bookmark,
    Follower,
    Likes,
    Posts,
    Profile,
    ReportedPosts,
    Reposts,
    Users,
)
from settings import Settings
from modules import (
    PUBLIC_DIRECTORY_POSTS,
    USE_CLOUDINARY_STORAGE,
    aliased,
    delete,
    exists,
    func,
    functools,
    json,
    literal,
    make_response,
    or_,
    os,
    request,
    select,
    time,
    update,
    url_for,
    logging
)
from services.cloudinary_service import delete_media
from tasks import add_task_in_queue
from tasks.interface import like, mention, process_user_requests, reply
from tasks.interface import repost as repost_interface
from utils import (
    AppError,
    BadRequestError,
    ForbiddenError,
    InternalServerError,
    ResourceNotFoundError,
    SuccessResponse,
    UnAuthorizedError,
    datetime_utc,
    fname,
)

from .feed_repository import _query_posts

Log = logging.getLogger(__name__)


def _create_post(
    user_id: int,
    text: str | None,
    tags: str | None,
    media_url: str | None,
    media_public_id: str | None,
    file_type: str | None,
    file_extension: str | None,
    age_rating: str,
    category: int,
    parent_post_id: int | None = None,
    is_reply: bool = False,
    visibility: bool = True,
    replying_to: list[str] | None = None,
):
    session = SessionLocal()
    try:
        new_post = Posts(
            user_id=user_id,
            text=text,
            tags=tags,
            media_url=media_url,
            media_public_id=media_public_id,
            file_type=file_type,
            file_extension=file_extension,
            visibility=visibility,
            age_rating=age_rating,
            category=category,
            is_reply=is_reply,
            parent_post_id=parent_post_id,
            replying_to=replying_to,
        )
        session.add(new_post)
        session.commit()
        session.refresh(new_post)

        # Create mention notification

        # If the post is a reply, create reply notifications for the users being replied to
        if is_reply:
            add_task_in_queue(
                functools.partial(
                    reply,
                    parent_post_id=parent_post_id,
                    post_id=new_post.id,
                    mentioned_usernames_by_system=replying_to,
                    mentioned_by_user_id=user_id,
                    text=text
                    or "",  # If text is None, pass an empty string to avoid issues in the mention function
                )
            )
        else:
            # Send notification to mentioned users in the post
            if text:
                add_task_in_queue(
                    functools.partial(
                        mention,
                        mentioned_by_user_id=user_id,
                        post_id=new_post.id,
                        text=text,
                    )
                )
        # process bot service if bot is tagged
        if text:
            add_task_in_queue(
                functools.partial(
                    process_user_requests,
                    text=text,
                    current_post_id=new_post.id,
                    replying_to=replying_to,
                    parent_post_id=parent_post_id,
                )
            )
        return SuccessResponse(
            message="post upload successfully", status_code=200, data={}
        )
    except AppError:
        session.rollback()
        raise
    except Exception as e:
        session.rollback()
        raise InternalServerError("Error while uploading post to database") from e
    finally:
        session.close()


def _post_toggle_like(session_user_id: int, post_id: int):
    session = SessionLocal()
    try:
        is_already_liked = (
            session.query(Likes)
            .filter(Likes.user_id == session_user_id, Likes.post_id == post_id)
            .first()
        )
        if not is_already_liked:
            # add like to post
            like_post = Likes(post_id=post_id, user_id=session_user_id)
            session.add(like_post)
            session.commit()
            # Notify the post owner
            add_task_in_queue(functools.partial(like, post_id, session_user_id))
            return SuccessResponse(
                data={"is_liked": True},
                message="Post liked successfully",
                status_code=201,
            )
        else:
            # remove like from post
            de_like = delete(Likes).filter(
                Likes.user_id == session_user_id, Likes.post_id == post_id
            )
            session.execute(de_like)
            session.commit()
            return SuccessResponse(
                data={"is_liked": False},
                message="Post like removed successfully",
                status_code=201,
            )

    except Exception as e:
        session.rollback()
        raise InternalServerError("Error while toggling post like") from e
    finally:
        session.close()


def _post_toggle_bookmark(session_user_id: int, post_id: int):
    session = SessionLocal()
    try:
        is_already_bookmarked = (
            session.query(Bookmark)
            .filter(Bookmark.user_id == session_user_id, Bookmark.post_id == post_id)
            .first()
        )
        if not is_already_bookmarked:
            # Add bookmark to user
            bookmark_post = Bookmark(post_id=post_id, user_id=session_user_id)
            session.add(bookmark_post)
            session.commit()
            return SuccessResponse(
                data={"is_bookmarked": True},
                message="Post bookmarked successfully",
                status_code=201,
            )

        else:
            # Remove row from Bookmark
            de_like = delete(Bookmark).filter(
                Bookmark.user_id == session_user_id, Bookmark.post_id == post_id
            )
            session.execute(de_like)
            session.commit()
            return SuccessResponse(
                data={"is_bookmarked": False},
                message="Post bookmark removed successfully",
                status_code=201,
            )
    except Exception as e:
        session.rollback()
        raise InternalServerError("Error while bookmarking post") from e
    finally:
        session.close()


def _delete_post(post_id: int, session_user_id: int):
    # TODO : Handle edge case
    session = SessionLocal()
    try:
        post = (
            session.query(Posts).filter_by(id=post_id, user_id=session_user_id).first()
        )
        # Check ownership of the post
        if not post:
            raise UnAuthorizedError("You do not have permission to delete this post")
        """
        # Delete the media
        if USE_CLOUDINARY_STORAGE:
            delete_media([result.media_public_id])
        else:
            filepath = os.path.join(
                PUBLIC_DIRECTORY_POSTS, f"{result.media_public_id}.{result.file_type}"
            )
            if os.path.exists(filepath):
                os.remove(filepath)
        session.delete(result)
        """
        post.is_deleted = True
        post.deleted_at = datetime_utc()
        session.commit()
    except AppError:
        session.rollback()
        raise
    except Exception as e:
        session.rollback()
        raise InternalServerError("Error while deleting post") from e
    finally:
        session.close()


def _repost_post(post_id: int, session_user_id: int):
    session = SessionLocal()
    # Toggle repost
    try:
        is_repost = (
            session.query(Reposts)
            .filter_by(post_id=post_id, user_id=session_user_id)
            .first()
        )
        if is_repost:
            stmt = delete(Reposts).where(
                Reposts.post_id == post_id, Reposts.user_id == session_user_id
            )
            session.execute(stmt)
            session.commit()
            add_task_in_queue(
                functools.partial(
                    repost_interface,
                    post_id=post_id,
                    session_user_id=session_user_id,
                )
            )
            return SuccessResponse(
                data={"is_reposted": False},
                message="Post repost removed successfully",
                status_code=201,
            )

        else:
            repost = Reposts(post_id=post_id, user_id=session_user_id)
            session.add(repost)
            session.commit()
            return SuccessResponse(
                data={"is_reposted": True},
                message="Post reposted successfully",
                status_code=201,
            )

    except AppError:
        session.rollback()
        raise

    except Exception as e:
        session.rollback()
        raise InternalServerError("Error while reposting post") from e
    finally:
        session.close()


def _update_post(
    post_id: int,
    session_user_id: int,
    title: str | None = None,
    tags: str | None = None,
    age_rating: AgeRating | None = None,
    category: int | None = None,
    visibility: bool | None = None,
):
    session = SessionLocal()
    try:
        # Check ownership of this post
        post = session.query(Posts).filter(Posts.id == post_id).first()
        if not post or post.user_id != session_user_id:
            raise UnAuthorizedError("You do not have permission to update this post")

        update_value = {}
        if title:
            update_value["text"] = title
        if tags:
            update_value["tags"] = tags
        if age_rating:
            update_value["age_rating"] = age_rating
        if category:
            update_value["category"] = category
        if visibility is not None:
            update_value["visibility"] = visibility

        stmt = update(Posts).where(Posts.id == post_id).values(update_value)
        session.execute(stmt)
        session.commit()
    except AppError:
        session.rollback()
        raise
    except Exception as e:
        session.rollback()
        raise InternalServerError("Error while updating post") from e
    finally:
        session.close()


def _user_posts(
    username: str,
    session_user_id: int | None = None,
    category: int | None = None,
    order_by="recent",
    fetch_template: bool = False,
    fetch_bookmarked: bool = False,
    limit: int = 10,
    offset: int = 0,
):
    session = SessionLocal()
    """
    Check if user is logged and session_user_id = username then fetch private posts too
    if user is logged but session_user_id != username then fetch public posts only
    else fetch public posts only
    """
    redis_key = f"user_posts:{username}:{session_user_id}:{category}:{order_by}:{fetch_template}:{fetch_bookmarked}:{limit}:{offset}"

    cached_result = redis_client.get(redis_key)

    if cached_result:
        _posts = json.loads(cached_result)
        Log.info(f"Cache hit for user_posts: {redis_key}")
        return SuccessResponse(
            data=_posts, message="Fetched user's post", status_code=200
        )

    try:
        conditions = []
        if fetch_template:
            conditions.append(Posts.is_template)

        if not session_user_id:
            conditions.append(Posts.visibility)

        conditions.append(Users.username == username)

        user = session.query(Users).where(Users.username == username).first()
        if not user:
            raise ResourceNotFoundError("User not found")
        if user.account_status == "suspended":
            raise ForbiddenError("Account is suspended")
        if user.account_status == "deleted":
            raise ForbiddenError("Account is deleted")
        if user.account_status == "banned":
            raise ForbiddenError("Account is banned")

        if fetch_bookmarked:
            conditions.append(Bookmark.user_id == user.id)

        posts = _query_posts(
            conditions=conditions,
            offset=offset,
            limit=limit,
            session_user_id=session_user_id,
        )
        redis_client.set(redis_key, json.dumps(posts), ex=100)

        Log.info(f"Cache miss for user_posts: {redis_key}")

        return SuccessResponse(
            data=posts, message="Fetched user's post", status_code=200
        )
    except AppError:
        raise
    except Exception as e:
        raise InternalServerError("Error while fetching user's posts") from e


def _get_post_media(
    post_id: int,
) -> tuple[str, str, str, str] | None:
    session = SessionLocal()
    try:
        post = (
            session.query(
                Posts.text,
                Posts.media_url,
                Posts.media_public_id,
                Posts.file_extension,
            )
            .filter(Posts.id == post_id)
            .first()
        )
        if not post:
            return None
        return tuple(post)
    except Exception as e:
        raise InternalServerError("Error while fetching post media url") from e
    finally:
        session.close()


def _get_post_by_id(
    post_id: int,
    session_user_id: int | None = None,
):
    session = SessionLocal()
    redis_key = f"post:{post_id}"
    post = redis_client.get(redis_key)
    if post:
        Log.info(f"Redis hit for post id: {post_id}")
        return SuccessResponse(
            message="Post retrieved successfully",
            data=json.loads(post),
            status_code=200,
        )
    try:
        conditions = []
        # Fetch post by ID
        conditions.append(Posts.id == post_id)
        conditions.append(Posts.is_deleted == False)

        # Check post visibility
        if session_user_id:
            # Check owner of the post
            post = (
                session.query(Posts)
                .where(Posts.id == post_id, Posts.is_deleted == False)
                .first()
            )

            if not post:
                raise ResourceNotFoundError("Post not found")

            if post.user_id == session_user_id:
                # Give the access to the private post to owner
                # Note : implement superadmin and moderator can access private post for enquiry
                pass
            else:
                # Check whether post's visibility is true or false
                if not post.visibility:
                    raise ForbiddenError("Post is private")
        else:
            conditions.append(Posts.visibility == True)

        posts = _query_posts(
            conditions=conditions,
            session_user_id=session_user_id,
        )
        Log.info(f"Redis miss for post id: {post_id}")
        if posts:
            if len(posts) == 0:
                return SuccessResponse(
                    message="No post dosen't exists",
                    data={},
                    status_code=204,
                )

            redis_client.set(redis_key, json.dumps(posts[0]), 300)
            return SuccessResponse(
                message="Post retrieved successfully",
                data=posts[0],
                status_code=200,
            )
        else:
            raise ResourceNotFoundError("Post not found")
    except AppError:
        session.rollback()
        raise
    except Exception as e:
        raise InternalServerError("Error while fetching posts by id") from e
    finally:
        session.close()


def _get_post_replies(
    post_id: int,
    session_user_id: int | None = None,
    limit: int = 10,
    offset: int = 0,
):
    session = SessionLocal()
    redis_key = f"post:{post_id}:{offset}:{limit}:{session_user_id}"

    replies = redis_client.get(redis_key)
    if replies:
        Log.info(f"Redis hit for post replies :{post_id}")
        return SuccessResponse(
            message="Post retrieved successfully",
            data=json.loads(replies),
            status_code=200,
        )

    try:
        conditions = [
            Posts.parent_post_id == post_id,
            Posts.is_deleted == False,
            Posts.visibility,  # Fetch only public posts
            Posts.is_reply,  # `not Posts.is_reply` is not working as false
        ]

        replies = _query_posts(
            conditions=conditions,
            offset=offset,
            limit=limit,
            session_user_id=session_user_id,
        )

        if replies:
            redis_client.set(redis_key, json.dumps(replies), ex=100)
            Log.info(f"Redis: miss replies for post :{post_id}")
            return SuccessResponse(
                message="Post retrieved successfully",
                data=replies,
                status_code=200,
            )
        else:
            return SuccessResponse(
                message="Post retrieved successfully",
                data=[],
                status_code=200,
            )
    except AppError:
        session.rollback()
        raise
    except Exception as e:
        raise InternalServerError("Error while fetching posts by id") from e
    finally:
        session.close()


def _report_post(session_user_id: int, post_id: int, reason: str):
    session = SessionLocal()
    try:
        post = ReportedPosts(
            reported_by=session_user_id, post_id=post_id, description=reason
        )
        session.add(post)
        session.commit()

        return SuccessResponse(
            data={}, message="Post reported successfully", status_code=201
        )
    except AppError:
        session.rollback()
        raise
    except Exception as e:
        session.rollback()
        raise InternalServerError("Error while reporting post") from e
    finally:
        session.close()


def _get_post_liked_users(
    post_id: int,
    session_user_id: int | None = None,
    limit: int = 10,
    offset: int = 0,
):
    session = SessionLocal()
    post = (
        session.query(Posts)
        .filter(Posts.id == post_id, Posts.visibility == True)
        .first()
    )
    if not post:
        raise ResourceNotFoundError("Post not found")
    session.close()

    join_model = Likes
    join_condition = Users.id == Likes.user_id
    where_condition = [Likes.post_id == post_id]
    return _fetch_post_users(
        join_model, join_condition, where_condition, session_user_id, limit, offset
    )


def _get_post_reposted_users(
    post_id: int,
    session_user_id: int | None = None,
    limit: int = 10,
    offset: int = 0,
):
    session = SessionLocal()
    post = (
        session.query(Posts)
        .filter(Posts.id == post_id, Posts.visibility == True)
        .first()
    )
    if not post:
        raise ResourceNotFoundError("Post not found")
    session.close()
    join_model = Reposts
    join_condition = Users.id == Reposts.user_id
    where_condition = [Reposts.post_id == post_id]
    return _fetch_post_users(
        join_model, join_condition, where_condition, session_user_id, limit, offset
    )


def _get_post_reqouted_users(
    post_id: int,
    session_user_id: int | None = None,
    limit: int = 10,
    offset: int = 0,
):
    join_model = Posts
    join_condition = Users.id == Posts.user_id
    where_condition = [Posts.parent_post_id == post_id, Posts.visibility == True]
    return _fetch_post_users(
        join_model, join_condition, where_condition, session_user_id, limit, offset
    )


def _get_post_bookmarked_users(
    post_id: int,
    session_user_id: int | None = None,
    limit: int = 10,
    offset: int = 0,
):
    session = SessionLocal()
    post = (
        session.query(Posts)
        .filter(Posts.id == post_id, Posts.visibility == True)
        .first()
    )
    if not post:
        raise ResourceNotFoundError("Post not found")
    session.close()
    join_model = Bookmark
    join_condition = Users.id == Bookmark.user_id
    where_condition = [
        Bookmark.post_id == post_id,
    ]  # Changed Bookmark.user_id to Bookmark.post_id
    return _fetch_post_users(
        join_model, join_condition, where_condition, session_user_id, limit, offset
    )


def _fetch_post_users(
    join_model,
    join_condition,
    where_condition,
    session_user_id: int | None,
    limit: int = 10,
    offset: int = 0,
):
    session = SessionLocal()
    start = time.perf_counter()
    try:
        redis_key = f"post-detail:{request.path}:{request.remote_addr}"

        cached_data = redis_client.get(redis_key)
        if cached_data:
            fetched_users = json.loads(cached_data)
            Log.info(
                f"Redis hit post's interected users: {(time.perf_counter() - start) * 1000:.2f} ms"
            )
            return SuccessResponse(
                data=fetched_users, message="Fetched data", status_code=200
            )
        stmt = (
            (
                select(
                    Users.id,
                    Users.username,
                    Users.name,
                    Profile.media_url,
                    Profile.media_public_id,
                    Profile.file_extension,
                    Profile.file_type,
                    select(Follower)
                    .where(
                        Follower.user_id == Users.id,
                        Follower.follower_id == session_user_id,
                    )
                    .exists()
                    .label("is_following")
                    if session_user_id
                    else literal(False).label("is_following"),
                )
                .join_from(Users, Profile, Users.id == Profile.user_id)
                .join_from(Users, join_model, join_condition)
            )
            .where(*where_condition)
            .limit(limit)
            .offset(offset)
        )
        result = session.execute(stmt).all()

        Log.info(
            f"DB miss post's interected users: {(time.perf_counter() - start) * 1000:.2f} ms"
        )
        fetched_users = [
            {
                "user_id": user.id,
                "username": user.username,
                "name": user.name,
                "profile_img_url": user.media_url
                if USE_CLOUDINARY_STORAGE
                else f"{Settings.API_ROOT_URL or (request.host_url)[:-1]}{url_for('return_assets.serve_image', filename=fname(user.media_public_id, user.file_extension))}",
                "file_extension": user.file_extension,
                "file_type": user.file_type,
                "is_following": user.is_following,
            }
            for user in result
        ]
        redis_client.set(redis_key, json.dumps(fetched_users), ex=800)
        return SuccessResponse(
            data=fetched_users, message="Fetched data", status_code=200
        )

    finally:
        session.close()


def _mark_post_as_template(session_user_id: int, post_id: int):
    session = SessionLocal()
    try:
        post = (
            session.query(Posts)
            .filter_by(
                id=post_id,
                user_id=session_user_id,
            )
            .first()
        )
        if not post:
            raise ResourceNotFoundError("Post not found")
        if post.is_template:
            post.is_template = False
        else:
            post.is_template = True
        session.commit()
        session.refresh(post)

        return SuccessResponse(
            data={"is_template": post.is_template},
            message="Post marked as template"
            if post.is_template
            else "Post unmarked as template",
            status_code=200,
        )
    except AppError:
        raise
    except Exception as e:
        raise InternalServerError("Error while marking post as template") from e
    finally:
        session.close()
