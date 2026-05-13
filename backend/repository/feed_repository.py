from backend.database import engine
from backend.models import Bookmark, Category, Likes, Posts, Profile, Reposts, Users
from backend.modules import (
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

Session = sessionmaker(bind=engine)
session = Session()


def _get_home_feed(
    category: list = [],
    offset: int = 0,
    limit: int = 10,
    fetch_template: bool = False,
    session_user_id: int | None = None,
):
    # Fetch only public posts and isReply false
    conditions = [Posts.visibility, Posts.is_reply.is_(False)]
    if fetch_template:
        conditions.append(Posts.is_template.is_(True))
    feed = query_posts(conditions, category, offset, limit, session_user_id)
    if feed and len(feed) >= 0:
        return make_response({"payload": feed}, 200)
    else:
        return make_response({"payload": []}, 200)


def _query_posts(
    conditions,
    category: list = [],
    offset: int = 0,
    limit: int = 10,
    session_user_id: int | None = None,
):
    """
    Global feed and post and replie query function
    """
    # Get feed data from database alog with userName of author of post
    like = aliased(Likes)
    likeCount = (
        select(func.count(like.user_id))
        .where(like.post_id == Posts.id)
        .correlate(Posts)
        .scalar_subquery()
    )
    repost = aliased(Reposts)
    repostCount = (
        select(func.count(repost.user_id))
        .where(repost.post_id == Posts.id)
        .correlate(Posts)
        .scalar_subquery()
    )
    bookmark = aliased(Bookmark)
    bookmarkCount = (
        select(func.count(bookmark.userID))
        .where(bookmark.postID == Posts.id)
        .correlate(Posts)
        .scalar_subquery()
    )

    reply = aliased(Posts)
    repliesCount = (
        select(func.count(reply.id))
        .where(reply.parentPostID == Posts.id, reply.isReply.is_(True))
        .scalar_subquery()
    )
    stmt = (
        select(
            Users.userName,
            Posts,
            Profile.mediaUrl,
            Profile.mediaPublicID,
            Profile.fileExtension,
            likeCount.label("likeCount"),
            repostCount.label("repostCount"),
            bookmarkCount.label("bookmarkCount"),
            repliesCount.label("replieCount"),
            exists(
                select(Likes).where(
                    Likes.postID == Posts.id, Likes.userID == session_user_id
                )
            ).label("isLiked"),
            exists(
                select(Bookmark).where(
                    Bookmark.postID == Posts.id, Bookmark.userID == session_user_id
                )
            ).label("isBookmarked"),
            exists(
                select(Reposts).where(
                    Reposts.postID == Posts.id, Reposts.userID == session_user_id
                )
            ).label("isReposted"),
        )
        .join_from(Users, Posts)
        .join_from(Users, Profile)
        .where(*conditions)
        .limit(limit)
        .offset(offset)
    )
    getFeed = session.execute(stmt).all()

    # Close the session
    session.close()
    try:
        feedObj = [
            {
                "userName": feed[0],
                "postID": feed[1].id,
                "userID": feed[1].userID,
                "title": feed[1].text,
                "tags": feed[1].tags,
                "replyingTo": feed[1].replyingTo,
                "fileType": feed[1].fileType,
                "fileExtension": feed[1].fileExtension,
                "visibility": feed[1].visibility,
                "parentPostID": _getParentPost(feed[1].parentPostID, session_user_id)
                if not feed[1].isReply
                else None,  # Check if post's 'isReply=True' send None because
                "createdAt": feed[1].createdAt,
                "ageRating": feed[
                    1
                ].ageRating.value,  # Return Enum class from db and get its value from 'ageRating': <PostAgeRating.pg13: 'pg13'>,
                "category": feed[1].category,
                "isTemplate": feed[1].isTemplate,
                "postMediaUrl": feed[1].mediaUrl
                if USE_CLOUDINARY_STORAGE
                else f"{API_ROOT_URL}{url_for('postMedia.servePostMedia', fileName=f'{feed[1].mediaPublicID}.{feed[1].fileExtension}')}",
                "profileImgUrl": feed[2]
                if USE_CLOUDINARY_STORAGE
                else f"{API_ROOT_URL}{url_for('profileImage.serveImage', fileName=f'{feed[3]}.{feed[4]}')}",
                "likeCount": feed[5],
                "repostCount": feed[6],
                "bookmarkCount": feed[7],
                "replieCount": feed[8],
                "isLiked": feed[9],
                "isBookmarked": feed[10],
                "isReposted": feed[11],
            }
            for feed in getFeed
        ]

        return feedObj

    except Exception as e:
        raise Exception(e)


def _getParentPost(postID: int, session_user_id: int | None = None):
    try:
        conditions = []
        # Fetch post by ID
        conditions.append(Posts.id == postID)

        # Check post visibility
        if session_user_id:
            # Check owner of the post
            post = session.query(Posts).where(Posts.id == postID).first()
            if not post:
                return {"error": "Post not found"}

            if not post.userID == session_user_id:
                # Check whether post's visibility is true or false
                if not post.visibility:
                    return {"error": "Post is private"}

                # Fetch only public posts
                conditions.append(Posts.visibility)

        stmt = (
            select(
                Users.userName,
                Posts,
                Profile.mediaUrl,
                Profile.mediaPublicID,
                Profile.fileExtension,
            )
            .join_from(Users, Posts)
            .join_from(Users, Profile)
            .where(*conditions)
        )

        result = session.execute(stmt).fetchone()
        if not result:
            return {"error": "Post not found"}

        post = {
            "userName": result[0],
            "postID": result[1].id,
            "title": result[1].text,
            "userID": result[1].userID,
            "fileType": result[1].fileType,
            "mediaPublicID": result[1].mediaPublicID,
            "fileExtension": result[1].fileExtension,
            "createdAt": result[1].createdAt,
            "ageRating": result[
                1
            ].ageRating.value,  # Return Enum class from db and get its value from
            "postMediaUrl": result[1].mediaUrl
            if USE_CLOUDINARY_STORAGE
            else f"{API_ROOT_URL}{url_for('postMedia.servePostMedia', fileName=f'{result[1].mediaPublicID}.{result[1].fileExtension}')}",
            "profileImgUrl": result[2]
            if USE_CLOUDINARY_STORAGE
            else f"{API_ROOT_URL}{url_for('profileImage.serveImage', fileName=f'{result[3]}.{result[4]}')}",
        }
        return {"payload": post}
    except Exception as e:
        return {"error": "Internal Server Error"}
