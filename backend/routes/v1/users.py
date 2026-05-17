from config import API_ENDPOINTS
from middlewares.verify_client_request import verify_request_middleware
from modules import (
    ALLOWED_PROFILE_FILE_MIMETYPE,
    ALLOWED_PROFILE_FILE_SIZE,
    PUBLIC_DIRECTORY_PROFILES,
    USE_CLOUDINARY_STORAGE,
    Blueprint,
    make_response,
    os,
    request,
    secure_filename,
    uuid,
)
from repository.user_repository import (
    _add_follower,
    _block_user,
    _get_user_profile,
    _remove_follower,
    _report_user,
    _unblock_user,
    _update_profile_img,
    _update_user,
)
from utils import LoggedUser, SuccessResponse, upload_media

users_blueprint = Blueprint("users", __name__)

route = API_ENDPOINTS()


# /user/<string:username>
@users_blueprint.route(f"{route.user.route_name}", methods=route.user.methods)
@verify_request_middleware(route.user.route_name)
def user_get_profile_detail(logged_user: LoggedUser | None = None, *args, **kwargs):
    username: str | None = kwargs.get("username") or request.args.get("username")
    user_id = request.args.get("user_id")
    user_email: str | None = request.args.get("email_id")
    if not (username or user_id or user_email):
        return make_response(
            {"error": "Expect any value of username, user_iD, email_iD"}
        )

    if user_id:
        if not isinstance(user_id, int):
            return make_response({"error": f"Invalid id {user_id} datatype"}, 400)

    try:
        return _get_user_profile(
            _user_id=user_id,
            _username=username,
            _email=user_email,
            session_user_id=logged_user.user_id if logged_user else None,
        )
    except Exception as e:
        return make_response({"error": str(e)}, 500)


# /user/update
@users_blueprint.route(route.user_update.route_name, methods=route.user_update.methods)
@verify_request_middleware(route.user_update.route_name)
def usersUpdateInfo(logged_user: LoggedUser, *args, **kwargs):
    session_user_id = logged_user.user_id
    try:
        body = request.get_json()
        if not body:
            return make_response({"error": "Invalid request body"}, 400)

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
    except Exception as e:
        return make_response({"error": str(e)}, 500)


# /user/profileImg/update
@users_blueprint.route(
    route.user_change_profile.route_name, methods=route.user_change_profile.methods
)
@verify_request_middleware(route.user_change_profile.route_name)
def users_Update_profile_img(logged_user: LoggedUser, *args, **kwargs):
    try:
        profile_media_uid = str(uuid.uuid4())
        session_user_id = logged_user.user_id

        file = request.files["file"]
        file.seek(0, 2)  # move to end of file
        size = file.tell()  # get current position, which is file size in bytes
        file.seek(0)  # reset file pointer
        print(f"Actual file size: {(size / 1020) / 1024} MB")
        if file.mimetype not in ALLOWED_PROFILE_FILE_MIMETYPE:
            return make_response({"error": "Invalid file type"}, 400)
        if size > ALLOWED_PROFILE_FILE_SIZE.get(file.mimetype):
            return make_response(
                {
                    "error": f"File size exceeds limit, Please upload a smaller file below {ALLOWED_PROFILE_FILE_SIZE.get(file.mimetype) / 1024 / 1024} MB."
                },
                400,
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
    except Exception as e:
        return make_response({"error": f"{e}"}, 500)


# /user/delete
@users_blueprint.route(route.user_delete.route_name, methods=route.user_delete.methods)
@verify_request_middleware(route.user_delete.route_name)
def users_delete():
    raise NotImplementedError()


# /user/follower
@users_blueprint.route(
    route.user_remove_follower.route_name, methods=route.user_remove_follower.methods
)
@verify_request_middleware(route.user_remove_follower.route_name)
def remove_follower(logged_user: LoggedUser, *args, **kwargs):
    session_user_id = logged_user.user_id
    body = request.get_json()
    if isinstance(body, dict):
        target_user_id = body.get("user_id")
        if not isinstance(target_user_id, int):
            return make_response({"error": f"Invalid {target_user_id} datatype"})
        if target_user_id == session_user_id:
            return make_response({"error": "user can't unfollow himself"}, 409)
        else:
            return _remove_follower(session_user_id, target_user_id)

    else:
        return make_response({"error": "Expect json body"}, 401)


#
@users_blueprint.route(
    route.user_add_follower.route_name, methods=route.user_add_follower.methods
)
@verify_request_middleware(route.user_add_follower.route_name)
def add_follower(logged_user: LoggedUser, *agrs, **kwargs):
    session_user_id = logged_user.user_id
    target_user_id = kwargs.get("user_id")

    if not isinstance(target_user_id, int):
        return make_response({"error": f"Invalid {target_user_id} datatype"})
    if target_user_id == session_user_id:
        return make_response({"error": "user can't follow himself"}, 409)
    else:
        return _add_follower(session_user_id, target_user_id)


@users_blueprint.route(route.user_block.route_name, methods=route.user_block.methods)
@verify_request_middleware(route.user_block.route_name)
def block_user(logged_user: LoggedUser, *args, **kwargs):
    session_user_id = logged_user.user_id
    user_id = kwargs.get("user_id")
    if not user_id or not isinstance(user_id, int):
        return make_response({"error": f"Invalid user_id {user_id} datatype"}, 400)
    return _block_user(session_user_id, user_id)


@users_blueprint.route(
    route.user_unblock.route_name, methods=route.user_unblock.methods
)
@verify_request_middleware(route.user_unblock.route_name)
def unblock_user(logged_user: LoggedUser, *args, **kwargs):
    session_user_id = logged_user.user_id
    user_id = kwargs.get("user_id")
    if not user_id or not isinstance(user_id, int):
        return make_response({"error": f"Invalid user_id {user_id} datatype"}, 400)
    return _unblock_user(session_user_id, user_id)


@users_blueprint.route(
    route.user_report_users.route_name,
    methods=route.user_report_users.methods,
)
@verify_request_middleware(route.user_report_users.route_name)
def report_user(logged_user: LoggedUser, *args, **kwargs):
    session_user_id = logged_user.user_id
    user_id = kwargs.get("user_id")
    if not user_id or not isinstance(user_id, int):
        return make_response({"error": f"Invalid user_id {user_id} datatype"}, 400)
    reason = request.get_json().get("reason")
    return _report_user(session_user_id, user_id, reason or "")
