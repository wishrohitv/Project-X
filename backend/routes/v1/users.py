from config import API_ENDPOINTS
from middlewares import verify_request_middleware
from modules import (
    ALLOWED_PROFILE_FILE_MIMETYPE,
    ALLOWED_PROFILE_FILE_SIZE,
    PUBLIC_DIRECTORY_PROFILES,
    USE_CLOUDINARY_STORAGE,
    Blueprint,
    os,
    request,
    secure_filename,
    uuid,
)
from repository.user_repository import (
    _add_follower,
    _block_user,
    _get_user_avatar,
    _get_user_profile,
    _remove_follower,
    _report_user,
    _unblock_user,
    _update_profile_img,
    _update_user,
)
from services.cloudinary_service import upload_media
from utils import (
    BadRequestError,
    ConflictError,
    InternalServerError,
    LoggedUser,
    SuccessResponse,
)

users_blueprint = Blueprint("users", __name__)

route = API_ENDPOINTS()


# /users/<string:username>
@users_blueprint.route(f"{route.user.route_name}", methods=route.user.methods)
@verify_request_middleware(route.user)
def user_get_profile_detail(logged_user: LoggedUser | None = None, *args, **kwargs):
    username: str | None = kwargs["username"] or request.args.get("username")
    user_id = request.args.get("user_id")
    user_email: str | None = request.args.get("email_id")

    if not username and not user_id and not user_email:
        raise BadRequestError("Expect any value of username, user_id, email_id")

    if user_id:
        try:
            user_id = int(user_id)
        except:
            raise BadRequestError(f"Invalid id {user_id} datatype")

    return _get_user_profile(
        _user_id=user_id,
        _username=username,
        _email=user_email,
        session_user_id=logged_user.user_id if logged_user else None,
    )


# /user PUT
@users_blueprint.route(route.user_update.route_name, methods=route.user_update.methods)
@verify_request_middleware(route.user_update)
def users_update_info(logged_user: LoggedUser, *args, **kwargs):
    session_user_id = logged_user.user_id
    body = request.get_json()

    name = body.get("name")
    bio = body.get("bio")
    country = body.get("country")
    age = body.get("age")

    return _update_user(
        session_user_id=session_user_id,
        name=name,
        bio=bio,
        country=country,
        age=age,
    )


# /users/profile_img PUT
@users_blueprint.route(
    route.user_change_profile.route_name, methods=route.user_change_profile.methods
)
@verify_request_middleware(route.user_change_profile)
def users_Update_profile_img(logged_user: LoggedUser, *args, **kwargs):
    profile_media_uid = str(uuid.uuid4())
    session_user_id = logged_user.user_id

    file = request.files["file"]
    if not file:
        raise BadRequestError("No file provided")
    file.seek(0, 2)  # move to end of file
    size = file.tell()  # get current position, which is file size in bytes
    file.seek(0)  # reset file pointer

    if file.mimetype not in ALLOWED_PROFILE_FILE_MIMETYPE:
        raise BadRequestError("Invalid file type")
    if size > ALLOWED_PROFILE_FILE_SIZE.get(file.mimetype):
        raise BadRequestError(
            f"File size exceeds limit, Please upload a smaller file below {ALLOWED_PROFILE_FILE_SIZE[file.mimetype] / 1024 / 1024} MB."
        )

    file_extension = file.filename.split(".")[-1]
    _mediaUrl = None
    _media_public_id = None
    if USE_CLOUDINARY_STORAGE:
        cloud_response = upload_media(file=file.stream, public_id=profile_media_uid)
        _mediaUrl = cloud_response.get("url")
        _media_public_id = cloud_response.get("public_id")
    else:
        file.save(
            os.path.join(
                PUBLIC_DIRECTORY_PROFILES,
                secure_filename(f"{profile_media_uid}.{file_extension}"),
            )
        )
        _media_public_id = profile_media_uid
    return _update_profile_img(
        session_user_id=session_user_id,
        media_public_id=_media_public_id,
        file_extension=file_extension,
        file_type=file.mimetype.split("/")[0],
    )


# /user DELETE
@users_blueprint.route(route.user_delete.route_name, methods=route.user_delete.methods)
@verify_request_middleware(route.user_delete)
def users_delete():
    raise NotImplementedError()


# /users/<int:user_id>/follower DELETE
@users_blueprint.route(
    route.user_remove_follower.route_name, methods=route.user_remove_follower.methods
)
@verify_request_middleware(route.user_remove_follower)
def remove_follower(logged_user: LoggedUser, *args, **kwargs):
    session_user_id = logged_user.user_id
    target_user_id: int = kwargs["user_id"]
    if target_user_id == session_user_id:
        raise ConflictError("User can't unfollow himself")
    else:
        return _remove_follower(session_user_id, target_user_id)


# /users/<int:user_id>/follower POST
@users_blueprint.route(
    route.user_add_follower.route_name, methods=route.user_add_follower.methods
)
@verify_request_middleware(route.user_add_follower)
def add_follower(logged_user: LoggedUser, *agrs, **kwargs):
    session_user_id = logged_user.user_id
    target_user_id = kwargs["user_id"]

    if target_user_id == session_user_id:
        raise ConflictError("User can't follow himself")
    else:
        return _add_follower(session_user_id, target_user_id)


# /users/<int:user_id>/block POST
@users_blueprint.route(route.user_block.route_name, methods=route.user_block.methods)
@verify_request_middleware(route.user_block)
def block_user(logged_user: LoggedUser, *args, **kwargs):
    session_user_id = logged_user.user_id
    target_user_id = kwargs["user_id"]
    if target_user_id == session_user_id:
        raise ConflictError("User can't block himself")
    return _block_user(session_user_id, target_user_id)


# /users/<int:user_id>/block DELETE
@users_blueprint.route(
    route.user_unblock.route_name, methods=route.user_unblock.methods
)
@verify_request_middleware(route.user_unblock)
def unblock_user(logged_user: LoggedUser, *args, **kwargs):
    session_user_id = logged_user.user_id
    target_user_id = kwargs["user_id"]
    if target_user_id == session_user_id:
        raise ConflictError("User can't block himself")
    return _unblock_user(session_user_id, target_user_id)


# TODO : Improve reasons
# /users/<int:user_id>/report POST
@users_blueprint.route(
    route.user_report_users.route_name,
    methods=route.user_report_users.methods,
)
@verify_request_middleware(route.user_report_users)
def report_user(logged_user: LoggedUser, *args, **kwargs):
    session_user_id = logged_user.user_id
    target_user_id = kwargs["user_id"]

    reason = request.get_json().get("reason")
    return _report_user(session_user_id, target_user_id, reason or "")


# /users/<string:username>/avatar GET
@users_blueprint.route(
    route.user_avatar.route_name,
    methods=route.user_avatar.methods,
)
def send_avatar_url(username: str):
    return _get_user_avatar(username)
