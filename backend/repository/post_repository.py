from database import engine
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
from modules import (
    API_ROOT_URL,
    PUBLIC_DIRECTORY_POSTS,
    USE_CLOUDINARY_STORAGE,
    aliased,
    delete,
    exists,
    func,
    functools,
    make_response,
    or_,
    os,
    select,
    sessionmaker,
    update,
    url_for,
)
from tasks import add_task_in_queue, mention, reply
from utils import Log, delete_media

from .feed_repository import queryPosts

Session = sessionmaker(bind=engine)
session = Session()


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
        session.close()

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
        return make_response({"message": "post upload successfully"}, 200)
    except Exception as e:
        session.rollback()
        session.close()
        Log.critical(str(e))
        raise Exception(str(e))


def _post_toggle_like(session_user_id: int, post_id: int):
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
            session.close()
            return make_response(
                {"isLiked": True, "message": "Post liked successfully"}, 201
            )
        else:
            # remove like from post
            de_like = delete(Likes).filter(
                Likes.user_id == session_user_id, Likes.post_id == post_id
            )
            session.execute(de_like)
            session.commit()
            return make_response(
                {"isLiked": False, "message": "Post like removed successfully"}, 201
            )
    except Exception as e:
        session.rollback()
        raise Exception(str(e))


def _post_toggle_bookmark(session_user_id: int, post_id: int):
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
            session.close()
            return make_response(
                {"isBookmarked": True, "message": "Post bookmark successfully"}, 201
            )
        else:
            # Remove row from Bookmark
            de_like = delete(Bookmark).filter(
                Bookmark.user_id == session_user_id, Bookmark.post_id == post_id
            )
            session.execute(de_like)
            session.commit()
            return make_response(
                {
                    "isBookmarked": False,
                    "message": "Post bookmark removed successfully",
                },
                201,
            )
    except Exception as e:
        session.rollback()
        raise Exception(str(e))


def _delete_post(post_id: int, session_user_id: int):
    try:
        result = (
            session.query(Posts).filter_by(id=post_id, user_id=session_user_id).first()
        )
        # Check ownership of the post
        if not result:
            raise Exception("You do not have permission to delete this post")
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
        session.commit()
    except Exception as e:
        session.rollback()
        raise Exception(str(e))


def _repost_post(post_id: int, session_user_id: int):
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
            return make_response(
                {"message": "Post repost removed successfully", "is_reposted": False},
                201,
            )
        else:
            repost = Reposts(post_id=post_id, user_id=session_user_id)
            session.add(repost)
            session.commit()
            return make_response(
                {"message": "Post reposted successfully", "is_reposted": True}, 201
            )
    except Exception as e:
        session.rollback()
        raise Exception(str(e))


def _update_post(
    post_id: int,
    session_user_id: int,
    title: str | None = None,
    tags: str | None = None,
    age_rating: AgeRating | None = None,
    category: int | None = None,
    visibility: bool | None = None,
):
    try:
        # Check ownership of this post
        post = session.query(Posts).filter(Posts.id == post_id).first()
        if not post or post.user_id != session_user_id:
            raise Exception("You do not have permission to update this post")

        update_value = {}
        if title:
            update_value["title"] = title
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
    except Exception as e:
        session.rollback()
        raise Exception(str(e))


def _user_posts(
    user_name: str,
    session_user_id: int | None = None,
    category: int | None = None,
    order_by="recent",
    fetch_template: bool = False,
    fetch_bookmarked: bool = False,
    limit: int = 10,
    offset: int = 0,
):
    """
    Check if user is logged and session_user_id = user_name then fetch private posts too
    if user is logged but session_user_id != user_name then fetch public posts only
    else fetch public posts only
    """
    try:
        conditions = []
        if fetch_template:
            conditions.append(Posts.is_template)

        if not session_user_id:
            conditions.append(Posts.visibility)

        conditions.append(Users.username == user_name)

        user = session.query(Users).where(Users.username == user_name).first()
        if not user:
            return make_response({"error": "User not found"}, 404)
        if user.account_status == "suspended":
            return make_response({"error": "Account is suspended"}, 404)
        if user.account_status == "deleted":
            return make_response({"error": "Account is deleted"}, 404)
        if user.account_status == "banned":
            return make_response({"error": "Account is banned"}, 404)

        if fetch_bookmarked:
            conditions.append(Bookmark.user_id == user.id)

        posts = queryPosts(
            conditions=conditions,
            offset=offset,
            limit=limit,
            session_user_id=session_user_id,
        )
        if len(posts) > 0:
            return make_response({"payload": posts}, 200)
        else:
            return make_response({"payload": []}, 200)
    except Exception as e:
        print(f"Error fetching user posts: {e}")
        return make_response({"error": str(e)}, 500)


def _get_post_media(
    post_id: int,
    offset: int = 0,
    limit: int = 10,
) -> tuple[str, str, str, str] | None:
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
        print(f"Error fetching post media: {e}")
        return None


def _get_post_by_id_or_post_replies_by_id(
    post_id: int,
    session_user_id: int | None = None,
    fetch_replies: bool = False,
    limit: int = 10,
    offset: int = 0,
):
    conditions = []
    if fetch_replies:
        conditions.append(Posts.parent_post_id == post_id)
        conditions.append(
            Posts.is_reply
        )  # `not Posts.is_reply` is not working as false
        conditions.append(Posts.visibility)  # Fetch only public posts
    else:
        #  Fetch post by ID
        conditions.append(Posts.id == post_id)

        # Check post visibility
        if session_user_id:
            # Check owner of the post
            post = session.query(Posts).where(Posts.id == post_id).first()
            if not post:
                return make_response({"error": "Post not found"}, 404)

            if post.user_id == session_user_id:
                # Give the access to the private post to owner
                # Note : implement superadmin and moderator can access private post for enquiry
                conditions.append(not Posts.visibility)
            else:
                # Check whether post's visibility is true or false
                if not post.visibility:
                    return make_response({"error": "Post is private"}, 403)
                conditions.append(Posts.visibility)
    posts_or_replies = queryPosts(
        conditions=conditions,
        offset=offset,
        limit=limit,
        session_user_id=session_user_id,
    )
    if posts_or_replies:
        if len(posts_or_replies) == 0:
            return make_response(
                {
                    "payload": [],
                    "message": "No replies found or post dosen't exists",
                },
                200,
            )
        return make_response({"payload": posts_or_replies}, 200)
    else:
        return make_response({"error": "Post not found"}, 404)


def _reportPost(sessionUserID: int, postID: int, reason: str):
    try:
        post = ReportedPosts(
            reportedBy=sessionUserID, postID=postID, description=reason
        )
        session.add(post)
        session.commit()
        session.close()
        return make_response({"message": "Post reported successfully"}, 201)
    except Exception as e:
        session.rollback()
        session.close()
        print(e)
        return make_response({"error": f"{e}"}, 500)


def _get_post_liked_users(
    post_id: int,
    session_user_id: int | None = None,
    limit: int = 10,
    offset: int = 0,
):
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
    where_condition = [Posts.parent_post_id == post_id]
    return _fetch_post_users(
        join_model, join_condition, where_condition, session_user_id, limit, offset
    )


def _getPostBookmarkedUsers(
    postID: int,
    sessionUserID: int | None = None,
    limit: int = 10,
    offset: int = 0,
):
    joinModel = Bookmark
    joinConditon = Users.id == Bookmark.user_id
    whereConditon = [Bookmark.user_id == postID]
    return _fetch_post_users(
        joinModel, joinConditon, whereConditon, sessionUserID, limit, offset
    )


def _fetch_post_users(
    join_model,
    join_condition,
    where_condition,
    session_user_id: int | None,
    limit: int = 10,
    offset: int = 0,
):
    # TODO: prevent access of data if post is unavailable
    try:
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
                    exists(
                        select(Follower).where(
                            Follower.user_id == Users.id,
                            Follower.follower_id == session_user_id,
                        )
                    ).label("is_following"),
                )
                .join_from(Users, Profile, Users.id == Profile.id)
                .join_from(Users, join_model, join_condition)
            )
            .where(*where_condition)
            .limit(limit)
            .offset(offset)
        )
        result = session.execute(stmt).all()
        session.close()
        fetched_users = [
            {
                "user_id": user.id,
                "user_name": user.username,
                "name": user.name,
                "profile_img_url": user.media_url
                if USE_CLOUDINARY_STORAGE
                else f"{API_ROOT_URL}{url_for('profileImage.serveImage', file_name=f'{user.media_public_id}.{user.file_extension}')}",
                "media_public_id": user.media_public_id,
                "file_extension": user.file_extension,
                "file_type": user.file_type,
                "is_following": user.is_following,
            }
            for user in result
        ]
        return make_response({"payload": fetched_users}, 200)
    except Exception as e:
        return Exception(str(e))
