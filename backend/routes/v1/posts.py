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
    _get_post_bookmarked_users,
    _get_post_by_id_or_post_replies_by_id,
    _get_post_liked_users,
    _get_post_reposted_users,
    _get_post_reqouted_users,
    _post_toggle_bookmark,
    _post_toggle_like,
    _report_post,
    _repost_post,
    _update_post,
    _user_posts,
)
from utils import (
    BadRequestError,
    ConflictError,
    Log,
    LoggedUser,
    ResourceNotFoundError,
    SuccessResponse,
    UnAuthorizedError,
    upload_media,
)

posts_blueprint = Blueprint("posts", __name__)

route = API_ENDPOINTS()


# /posts/<string:username> GET
# Unlogged user can access public posts
@posts_blueprint.route(route.posts.route_name, methods=route.posts.methods)
@verify_request_middleware(route.posts.route_name)
def posts(logged_user: LoggedUser | None, *args, **kwargs):
    username: str = kwargs["username"]
    order_by = request.args.get("order_by")
    category = request.args.get("category")
    limit = request.args.get("limit", type=int, default=10)
    offset = request.args.get("offset", type=int, default=0)
    template = str(request.args.get("template", default="False")).lower() == "true"
    bookmark = str(request.args.get("bookmark", default="False")).lower() == "true"
    session_user_id: int | None = None if logged_user is None else logged_user.user_id

    return _user_posts(
        username=username,
        session_user_id=session_user_id,
        limit=limit,
        offset=offset,
        fetch_template=template,
        fetch_bookmarked=bookmark,
    )


# /posts/<int:post_id>/liked-users GET
@posts_blueprint.route(
    route.posts_liked_users.route_name,
    methods=route.posts_liked_users.methods,
)
@verify_request_middleware(route.posts_liked_users.route_name)
def post_liked_user(logged_user: LoggedUser | None, *args, **kwargs):
    post_id = kwargs["post_id"]
    session_user_id = logged_user.user_id if logged_user else None
    offset = request.args.get("offset", type=int, default=0)
    limit = request.args.get("limit", type=int, default=10)
    if session_user_id is None:
        # Only logged in users can see who liked a post
        raise UnAuthorizedError("User not logged in")
    if limit >= 20:
        raise BadRequestError("Limit must be less than or equal to 20")

    return _get_post_liked_users(post_id, session_user_id, offset, limit)


# /posts/<int:post_id>/bookmarked-users GET
@posts_blueprint.route(
    route.post_bookmarked_users.route_name,
    methods=route.post_bookmarked_users.methods,
)
@verify_request_middleware(route.post_bookmarked_users.route_name)
def postBookmarkedUser(logged_user: LoggedUser | None, *args, **kwargs):
    post_id = kwargs["post_id"]
    session_user_id = logged_user.user_id if logged_user else None
    offset = request.args.get("offset", type=int, default=0)
    limit = request.args.get("limit", type=int, default=10)
    if limit >= 20:
        raise BadRequestError("Limit must be less than or equal to 20")
    if session_user_id is None:
        # Only logged in users can see who liked a post
        raise UnAuthorizedError("User not logged in")

    return _get_post_bookmarked_users(post_id, session_user_id, offset, limit)


# /posts/<int:post_id>/reposted-users GET
@posts_blueprint.route(
    route.post_reposted_users.route_name,
    methods=route.post_reposted_users.methods,
)
@verify_request_middleware(route.post_reposted_users.route_name)
def postRepostedUser(logged_user: LoggedUser | None, *args, **kwargs):
    post_id = kwargs["post_id"]
    session_user_id = logged_user.user_id if logged_user else None
    offset = request.args.get("offset", type=int, default=0)
    limit = request.args.get("limit", type=int, default=10)
    if limit >= 20:
        raise BadRequestError("Limit must be less than or equal to 20")
    if session_user_id is None:
        # Only logged in users can see who liked a post
        raise UnAuthorizedError("User not logged in")

    return _get_post_reposted_users(post_id, session_user_id, limit, offset)


# /posts/<int:post_id>/qouted-users GET
@posts_blueprint.route(
    route.post_qouted_users.route_name,
    methods=route.post_qouted_users.methods,
)
@verify_request_middleware(route.post_qouted_users.route_name)
def postReqoutedUser(logged_user: LoggedUser | None, *args, **kwargs):
    post_id = kwargs["post_id"]
    session_user_id = logged_user.user_id if logged_user else None
    offset = request.args.get("offset", type=int, default=0)
    limit = request.args.get("limit", type=int, default=10)
    if limit >= 20:
        raise BadRequestError("Limit must be less than or equal to 20")
    if session_user_id is None:
        # Only logged in users can see who liked a post
        raise UnAuthorizedError("User not logged in")

    return _get_post_reqouted_users(post_id, session_user_id, limit, offset)


# /posts
@posts_blueprint.route(
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
        raise BadRequestError("Parent post ID is required for reply to a post")
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
                {"error": "post_replying_to must be a list of strings of usernames"},
                400,
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


# /posts/<int:post_id>/repost POST
@posts_blueprint.route(route.post_repost.route_name, methods=route.post_repost.methods)
@verify_request_middleware(route.post_repost.route_name)
def repost_post(logged_user: LoggedUser, *args, **kwargs):
    post_id = kwargs["post_id"]
    session_user_id = logged_user.user_id
    return _repost_post(session_user_id=session_user_id, post_id=post_id)


# /posts/<int:post_id>/like POST
@posts_blueprint.route(route.post_like.route_name, methods=route.post_like.methods)
@verify_request_middleware(route.post_like.route_name)
def post_toggle_like(logged_user: LoggedUser, *agrs, **kwargs):
    session_user_id = logged_user.user_id
    post_id = kwargs["post_id"]

    return _post_toggle_like(session_user_id=session_user_id, post_id=post_id)


# /posts/<int:post_id>/bookmark PUT
@posts_blueprint.route(
    route.post_bookmark.route_name, methods=route.post_bookmark.methods
)
@verify_request_middleware(route.post_bookmark.route_name)
def toggle_bookmark(logged_user: LoggedUser, *agrs, **kwargs):
    session_user_id = logged_user.user_id

    post_id = kwargs["post_id"]

    return _post_toggle_bookmark(session_user_id=session_user_id, post_id=post_id)


# /posts/<int:post_id> DELETE
@posts_blueprint.route(route.post_delete.route_name, methods=route.post_delete.methods)
@verify_request_middleware(route.post_delete.route_name)
def delete_post(logged_user: LoggedUser, *args, **kwargs):
    session_user_id = logged_user.user_id
    post_id = kwargs["post_id"]

    _delete_post(session_user_id=session_user_id, post_id=post_id)

    return SuccessResponse(
        message="Post deleted successfully", data={}, status_code=201
    )


# /posts/<int:post_id> PATCH
@posts_blueprint.route(route.post_update.route_name, methods=route.post_update.methods)
@verify_request_middleware(route.post_update.route_name)
def update_post(logged_user: LoggedUser, *args, **kwargs):
    session_user_id = logged_user.user_id
    post_id = kwargs["post_id"]

    body = request.json
    title = body.get("title")
    tags = body.get("tags")
    age_rating = body.get("age_rating")
    category = body.get("category")
    visibility = body.get("visibility")

    _update_post(
        session_user_id=session_user_id,
        post_id=post_id,
        title=title,
        tags=tags,
        age_rating=age_rating,
        category=category,
        visibility=visibility,
    )

    return SuccessResponse(
        message="Post updated successfully", data={}, status_code=200
    )


# /posts/<int:post_id> GET
@posts_blueprint.route(
    route.posts_by_id.route_name,
    methods=route.posts_by_id.methods,
)
@verify_request_middleware(route.posts_by_id.route_name)
def postsByID(logged_user: LoggedUser | None = None, *args, **kwargs):
    post_id = kwargs["post_id"]
    session_user_id: int | None = logged_user.user_id if logged_user else None

    return _get_post_by_id_or_post_replies_by_id(
        post_id=post_id, session_user_id=session_user_id
    )


# /posts/<int:post_id>/replies GET
@posts_blueprint.route(
    route.post_replies.route_name,
    methods=route.post_replies.methods,
)
@verify_request_middleware(route.post_replies.route_name)
def posts_replies(logged_user: LoggedUser | None = None, *args, **kwargs):
    post_id: int = kwargs["post_id"]

    return _get_post_by_id_or_post_replies_by_id(post_id=post_id, fetch_replies=True)


# /posts/<int:post_id>/report POST
@posts_blueprint.route(
    route.report_post.route_name,
    methods=route.report_post.methods,
)
@verify_request_middleware(route.report_post.route_name)
def report_post(logged_user: LoggedUser, *args, **kwargs):
    session_user_id = logged_user.user_id
    post_id: int = kwargs["post_id"]

    reason = request.get_json().get("reason")
    return _report_post(session_user_id=session_user_id, post_id=post_id, reason=reason)
