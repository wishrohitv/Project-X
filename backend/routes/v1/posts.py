from config import API_ENDPOINTS
from middlewares.verify_client_request import verify_request_middleware
from modules import (
    ALLOWED_POST_FILE_MIMETYPE,
    ALLOWED_POST_FILE_SIZE,
    PUBLIC_DIRECTORY_POSTS,
    USE_CLOUDINARY_STORAGE,
    Blueprint,
    json,
    make_response,
    os,
    request,
    secure_filename,
    uuid,
)
from repository.post_repository import (
    _create_post,
    _delete_post,
    _getPostBookmarkedUsers,
    _get_post_by_id_or_post_replies_by_id,
    _get_post_liked_users,
    _getPostRepostedUsers,
    _getPostReqoutedUsers,
    _postToggleBookmark,
    _postToggleLike,
    _reportPost,
    _repostPost,
    _updatePost,
    _userPosts,
)
from utils import Log, LoggedUser, upload_media

post_blueprint = Blueprint("posts", __name__)

route = API_ENDPOINTS()


# /posts/<string:userName>
# Unlogged user can access public posts
@post_blueprint.route(
    f"{route.posts.route_name}/<string:userName>", methods=route.posts.methods
)
@verify_request_middleware(route.posts.route_name)
def posts(logged_user: LoggedUser | None, *args, **kwargs):
    userName = kwargs.get("userName")
    orderBy = request.args.get("orderBy")
    category = request.args.get("category")
    limit = request.args.get("limit", type=int, default=10)
    offset = request.args.get("offset", type=int, default=0)
    template = str(request.args.get("template", default="False")).lower() == "true"
    bookmark = str(request.args.get("bookmark", default="False")).lower() == "true"
    session_user_id: int | None = None if logged_user is None else logged_user.user_id
    if not userName:
        return make_response({"error": "Invalid username"}, 400)
    try:
        return _userPosts(
            userName=userName,
            session_user_id=session_user_id,
            limit=limit,
            offset=offset,
            fetchTemplate=template,
            fetchBookmarked=bookmark,
        )
    except Exception as e:
        return make_response({"error": str(e), "message": "Internal server error"}, 500)


# /posts/liked-users
@post_blueprint.route(
    route.posts_liked_users.route_name,
    methods=route.posts_liked_users.methods,
)
@verify_request_middleware(route.posts_liked_users.route_name)
def post_liked_user(logged_user: LoggedUser | None, *args, **kwargs):
    post_id = kwargs.get("post_id")
    session_user_id = logged_user.user_id if logged_user else None
    offset = request.args.get("offset", type=int, default=0)
    limit = request.args.get("limit", type=int, default=10)
    if session_user_id is None:
        # Only logged in users can see who liked a post
        return make_response({"error": "User not logged in"}, 401)
    if not isinstance(post_id, int):
        return make_response({"error": "Invalid post ID"}, 400)
    if limit >= 20:
        return make_response({"error": "Limit must be less than or equal to 20"}, 400)
    try:
        return _get_post_liked_users(post_id, session_user_id, offset, limit)
    except Exception as e:
        return make_response({"error": str(e), "message": "Internal server error"}, 500)


@post_blueprint.route(
    f"{route.postBookmaredUsers.route_name}/<int:post_id>",
    methods=route.postBookmaredUsers.methods,
)
@verify_request_middleware(route.postBookmaredUsers.route_name)
def postBookmarkedUser(logged_user: LoggedUser | None, *args, **kwargs):
    post_id = kwargs.get("post_id")
    session_user_id = logged_user.user_id if logged_user else None
    offset = request.args.get("offset", type=int, default=0)
    limit = request.args.get("limit", type=int, default=10)
    if limit >= 20:
        return make_response({"error": "Limit must be less than or equal to 20"}, 400)
    if session_user_id is None:
        # Only logged in users can see who liked a post
        return make_response({"error": "User not logged in"}, 401)
    if not isinstance(post_id, int):
        return make_response({"error": "Invalid post ID"}, 400)
    try:
        return _getPostBookmarkedUsers(post_id, session_user_id, offset, limit)
    except Exception as e:
        return make_response({"error": str(e), "message": "Internal server error"}, 500)


@post_blueprint.route(
    f"{route.postRepostedUsers.route_name}/<int:post_id>",
    methods=route.postRepostedUsers.methods,
)
@verify_request_middleware(route.postRepostedUsers.route_name)
def postRepostedUser(logged_user: LoggedUser | None, *args, **kwargs):
    post_id = kwargs.get("post_id")
    session_user_id = logged_user.user_id if logged_user else None
    offset = request.args.get("offset", type=int, default=0)
    limit = request.args.get("limit", type=int, default=10)
    if limit >= 20:
        return make_response({"error": "Limit must be less than or equal to 20"}, 400)
    if session_user_id is None:
        # Only logged in users can see who liked a post
        return make_response({"error": "User not logged in"}, 401)
    if not isinstance(post_id, int):
        return make_response({"error": "Invalid post ID"}, 400)
    try:
        return _getPostRepostedUsers(post_id, session_user_id, limit, offset)
    except Exception as e:
        return make_response({"error": str(e), "message": "Internal server error"}, 500)


@post_blueprint.route(
    f"{route.postReqoutedUsers.route_name}/<int:post_id>",
    methods=route.postReqoutedUsers.methods,
)
@verify_request_middleware(route.postReqoutedUsers.route_name)
def postReqoutedUser(logged_user: LoggedUser | None, *args, **kwargs):
    post_id = kwargs.get("post_id")
    session_user_id = logged_user.user_id if logged_user else None
    offset = request.args.get("offset", type=int, default=0)
    limit = request.args.get("limit", type=int, default=10)
    if limit >= 20:
        return make_response({"error": "Limit must be less than or equal to 20"}, 400)
    if session_user_id is None:
        # Only logged in users can see who liked a post
        return make_response({"error": "User not logged in"}, 401)
    if not isinstance(post_id, int):
        return make_response({"error": "Invalid post ID"}, 400)
    try:
        return _getPostReqoutedUsers(post_id, session_user_id, limit, offset)
    except Exception as e:
        return make_response({"error": str(e), "message": "Internal server error"}, 500)


# /posts
@post_blueprint.route(
    route.post_upload_post.route_name, methods=route.post_upload_post.methods
)
@verify_request_middleware(route.post_upload_post.route_name)
def upload_posts(logged_user: LoggedUser, *args, **kwargs):
    session_user_id = logged_user.user_id

    is_reply = (
        str(request.args.get("is_reply", default="False", type=str)).lower() == "true"
    )
    parent_post_id = request.args.get("parent_post_id", default=None, type=int)

    if is_reply and not parent_post_id:
        return make_response(
            {
                "error": "Parent post ID is required for reply to a post",
                "message": "Bad request",
            },
            400,
        )
    try:
        # Handle files
        file = request.files.get(
            "files"
        )  # i.e. <FileStorage: 'mario-removebg-preview.png' ('image/png')>
        _media_public_id = str(
            uuid.uuid4()
        )  # Initially any random id otherwise None if file not found
        _file_type = None  # i.e "image/jpeg"
        _file_extension = None
        _media_url = None

        p_form = request.form
        post_visibility = p_form.get("post_visibility")
        post_title = p_form.get("post_title")
        post_replying_to = p_form.get(
            "post_replying_to"
        )  # List(string) of usernames and parse it in python list using json.loads
        post_tags = p_form.get("post_tags")
        post_visibility = (
            True if not post_visibility else post_visibility.lower() == "true"
        )
        post_age_rating = (p_form.get("age_rating") or "pg13").lower()

        if file:
            file_mime_type = file.mimetype
            _file_type = file_mime_type.split("/")[0]
            if file_mime_type in ALLOWED_POST_FILE_MIMETYPE:
                _file_extension = ALLOWED_POST_FILE_MIMETYPE.get(file_mime_type)

            else:
                return make_response(
                    {"error": f"unsupported file type {file_mime_type}"}, 401
                )
            file_size = file.stream.seek(0, os.SEEK_END)

            allowed_file_size = ALLOWED_POST_FILE_SIZE.get(file_mime_type)
            if not (file_size <= allowed_file_size):
                return make_response(
                    {
                        "error": "File size exceeded",
                        "message": f"File size must not exceed {allowed_file_size / 1024 / 1024} MB",
                    },
                    406,
                )
            # Move pointer to Zero
            file.stream.seek(0)  # Moves the file pointer back to the beginning

            if USE_CLOUDINARY_STORAGE:
                cloud_response = upload_media(
                    file=file.stream, public_id=_media_public_id
                )
                if not (cloud_response):
                    return make_response({"error": "Failed to upload media"}, 500)
                _media_url = cloud_response.get("url")
                _media_public_id = cloud_response.get("public_id")
            else:
                file.save(
                    os.path.join(
                        PUBLIC_DIRECTORY_POSTS,
                        secure_filename(f"{_media_public_id}.{_file_extension}"),
                    )
                )
        else:
            _media_public_id = None

        # Check if text and file both is not None
        if not post_title and not _media_public_id:
            return make_response({"error": "Text or file is required"}, 400)
        if post_title.strip() == "":
            return make_response({"error": "Text is required"}, 400)

        if post_replying_to and not isinstance(json.loads(post_replying_to), list):
            return make_response(
                {"error": "postReplyingTo must be a list of strings of usernames"}, 400
            )
        _create_post(
            user_id=session_user_id,
            text=post_title,
            tags=post_tags,
            visibility=post_visibility,
            file_type=_file_type,  # i.e "image/jpeg"
            file_extension=_file_extension,
            media_url=_media_url,
            media_public_id=_media_public_id,
            category=1,
            age_rating=post_age_rating,
            is_reply=is_reply,
            parent_post_id=parent_post_id,
            replying_to=json.loads(post_replying_to) if post_replying_to else None,
        )
        return make_response({"message": "post uploaded successfully"}, 201)
    except Exception as e:
        Log.error(f"Failed to upload post: {e}")
        return make_response({"error": f"{e}"}, 500)


# /posts/reposts
@post_blueprint.route(
    f"{route.repostPosts.route_name}/<int:post_id>", methods=route.repostPosts.methods
)
@verify_request_middleware(route.repostPosts.route_name)
def repostPost(logged_user: LoggedUser, *args, **kwargs):
    post_id = kwargs.get("post_id")
    session_user_id = logged_user.user_id
    if post_id is None or not isinstance(post_id, int):
        return make_response({"error": f"Invalid post ID {post_id} type"}, 400)
    return _repostPost(session_user_id=session_user_id, post_id=post_id)


# /posts/like
@post_blueprint.route(
    f"{route.postLike.route_name}/<int:post_id>", methods=route.postLike.methods
)
@verify_request_middleware(route.postLike.route_name)
def toggleLike(logged_user: LoggedUser, *agrs, **kwargs):
    session_user_id = logged_user.user_id

    post_id = kwargs.get("post_id")
    if post_id is None and not isinstance(post_id, int):
        return make_response({"error": "Invalid post ID"}, 400)
    try:
        return _postToggleLike(session_user_id=session_user_id, post_id=post_id)

    except Exception as e:
        return make_response({"error": str(e), "message": "Internal server error"}, 500)


# /posts/bookmark
@post_blueprint.route(
    f"{route.postBookmark.route_name}/<int:post_id>", methods=route.postBookmark.methods
)
@verify_request_middleware(route.postBookmark.route_name)
def toggleBookmark(logged_user: LoggedUser, *agrs, **kwargs):
    session_user_id = logged_user.user_id

    post_id = kwargs.get("post_id")
    if post_id is None and not isinstance(post_id, int):
        return make_response({"error": "Invalid post ID"}, 400)
    try:
        return _postToggleBookmark(session_user_id=session_user_id, post_id=post_id)

    except Exception as e:
        return make_response({"error": str(e), "message": "Internal server error"}, 500)


# /posts
@post_blueprint.route(
    route.post_delete.route_name}, methods=route.post_delete.methods
)
@verify_request_middleware(route.post_delete.route_name)
def delete_post(logged_user: LoggedUser, *args, **kwargs):
    session_user_id = logged_user.user_id
    post_id = kwargs.get("post_id")
    if post_id is None and not isinstance(post_id, int):
        return make_response({"error": f"Invalid post_id {post_id} datatype"}, 400)
    try:
        _delete_post(session_user_id=session_user_id, post_id=post_id)

        return make_response({"message": "Post deleted successfully"}, 201)
    except Exception as e:
        return make_response({"error": str(e), "message": "Internal server error"}, 500)


# /posts/update
@post_blueprint.route(route.post_update.route_name, methods=route.post_update.methods)
@verify_request_middleware(route.post_update.route_name)
def updatePost(logged_user: LoggedUser, *args, **kwargs):
    session_user_id = logged_user.user_id
    post_id = kwargs.get("post_id")
    if post_id is None and not isinstance(post_id, int):
        return make_response({"error": f"Invalid post_id {post_id} datatype"}, 400)
    try:
        body = request.json
        title = body.get("title")
        tags = body.get("tags")
        ageRating = body.get("ageRating")
        category = body.get("category")
        visibility = body.get("visibility")

        _updatePost(
            session_user_id=session_user_id,
            post_id=post_id,
            title=title,
            tags=tags,
            ageRating=ageRating,
            category=category,
            visibility=visibility,
        )

        return make_response({"message": "Post updated successfully"}, 201)
    except Exception as e:
        return make_response({"error": str(e), "message": "Internal server error"}, 500)


# /posts
@post_blueprint.route(
    f"{route.posts.route_name}/<int:post_id>",
    methods=route.posts.methods,
)
@verify_request_middleware(route.posts.route_name)
def postsByID(logged_user: LoggedUser | None = None, *args, **kwargs):
    post_id = kwargs.get("post_id")
    session_user_id: int | None = logged_user.user_id if logged_user else None
    if not post_id or not isinstance(post_id, int):
        return make_response({"error": "Missing post_id"}, 400)
    try:
        return _get_post_by_id_or_post_replies_by_id(
            post_id=post_id, session_user_id=session_user_id
        )
    except Exception as e:
        print(e)
        return make_response({"error": str(e), "message": "Internal server error"}, 500)


# /posts/<int:post_id>/replies
@post_blueprint.route(
    route.post_replies.route_name,
    methods=route.post_replies.methods,
)
@verify_request_middleware(route.post_replies.route_name)
def posts_replies(logged_user: LoggedUser | None = None, *args, **kwargs):
    post_id: int | None = kwargs.get("post_id")
    if not post_id:
        return make_response({"error": f"Invalid post id {post_id}"}, 400)
    try:
        return _get_post_by_id_or_post_replies_by_id(post_id=post_id, fetch_replies=True)
    except Exception as e:
        return make_response({"error": str(e), "message": "Internal server error"}, 500)


# /posts/report
@post_blueprint.route(
    f"{route.reportPost.route_name}/<int:post_id>",
    methods=route.reportPost.methods,
)
@verify_request_middleware(route.reportPost.route_name)
def reportPost(logged_user: LoggedUser, *args, **kwargs):
    session_user_id = logged_user.user_id
    post_id: int | None = kwargs.get("post_id")
    if not post_id:
        return make_response({"error": f"Invalid post id {post_id}"}, 400)
    try:
        reason = request.get_json().get("reason")
        return _reportPost(
            session_user_id=session_user_id, post_id=post_id, reason=reason
        )
    except Exception as e:
        return make_response({"error": str(e), "message": "Internal server error"}, 500)
