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
from repository.user_respository import (
    _addFollower,
    _blockUser,
    _getUserProfile,
    _removeFollower,
    _reportUser,
    _unblockUser,
    _updateProfileImg,
    _updateUser,
)
from utils import LoggedUser, SuccessResponse, upload_media

users_blueprint = Blueprint("users", __name__)

route = API_ENDPOINTS()


# /user/<string:username>
@users_blueprint.route(f"{route.user.route_name}", methods=route.user.methods)
@verify_request_middleware(route.user.route_name)
def user_get_profile_detail(loggedUser: LoggedUser | None = None, *args, **kwargs):
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
        return _getUserProfile(
            _user_id=user_id,
            _username=username,
            _email=user_email,
            session_user_id=loggedUser.user_id if loggedUser else None,
        )
    except Exception as e:
        return make_response({"error": str(e)}, 500)


# /user/update
@users_blueprint.route(route.user_update.route_name, methods=route.user_update.methods)
@verify_request_middleware(route.user_update.route_name)
def usersUpdateInfo(loggedUser: LoggedUser, *args, **kwargs):
    sessionUserID = loggedUser.userID
    try:
        body = request.get_json()
        if not body:
            return make_response({"error": "Invalid request body"}, 400)

        name = body.get("name")
        bio = body.get("bio")
        country = body.get("country")
        age = body.get("age")

        return _updateUser(
            sessionUserID=sessionUserID, name=name, bio=bio, country=country, age=age
        )
    except Exception as e:
        return make_response({"error": str(e)}, 500)


# /user/profileImg/update
@users_blueprint.route(
    route.user_change_profile.route_name, methods=route.user_change_profile.methods
)
@verify_request_middleware(route.user_change_profile.route_name)
def users_UpdateProfileImg(loggedUser: LoggedUser, *args, **kwargs):
    try:
        profileMediaUid = str(uuid.uuid4())
        sessionUserID = loggedUser.userID

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

        fileExtension = file.filename.split(".")[-1]
        _mediaUrl = None
        _mediaPublicID = None
        if USE_CLOUDINARY_STORAGE:
            cloudResponse = upload_media(file=file.stream, public_id=profileMediaUid)
            _mediaUrl = cloudResponse.get("url")
            _mediaPublicID = cloudResponse.get("public_id")
        else:
            file.save(
                os.path.join(
                    PUBLIC_DIRECTORY_PROFILES,
                    secure_filename(f"{profileMediaUid}.{fileExtension}"),
                )
            )
            _mediaPublicID = profileMediaUid
        return _updateProfileImg(
            sessionUserID=sessionUserID,
            mediaPublicID=_mediaPublicID,
            fileExtension=fileExtension,
            fileType=file.mimetype.split("/")[0],
        )
    except Exception as e:
        return make_response({"error": f"{e}"}, 500)


# /user/delete
@users_blueprint.route(route.user_delete.route_name, methods=route.user_delete.methods)
@verify_request_middleware(route.user_delete.route_name)
def usersDelete():
    raise NotImplementedError()


# /user/follower
@users_blueprint.route(
    route.user_remove_follower.route_name, methods=route.user_remove_follower.methods
)
@verify_request_middleware(route.user_remove_follower.route_name)
def removeFollower(loggedUser: LoggedUser, *args, **kwargs):
    sessionUserID = loggedUser.user_id
    body = request.get_json()
    if isinstance(body, dict):
        targetUserID = body.get("userID")
        if not isinstance(targetUserID, int):
            return make_response({"error": f"Invalid {targetUserID} datatype"})
        if targetUserID == sessionUserID:
            return make_response({"error": "user can't unfollow himself"}, 409)
        else:
            return _removeFollower(sessionUserID, targetUserID)

    else:
        return make_response({"error": "Expect json body"}, 401)


# /user/follower
@users_blueprint.route(
    route.user_add_follower.route_name, methods=route.user_add_follower.methods
)
@verify_request_middleware(route.user_add_follower.route_name)
def addFollower(loggedUser: LoggedUser, *agrs, **kwargs):
    sessionUserID = loggedUser.userID
    body = request.get_json()
    if isinstance(body, dict):
        targetUserID = body.get("userID")
        if not isinstance(targetUserID, int):
            return make_response({"error": f"Invalid {targetUserID} datatype"})
        if targetUserID == sessionUserID:
            return make_response({"error": "user can't follow himself"}, 409)
        else:
            return _addFollower(sessionUserID, targetUserID)

    else:
        return make_response({"error": "Expect json body"}, 401)


@users_blueprint.route(
    f"{route.user_block.route_name}/<int:userID>", methods=route.user_block.methods
)
@verify_request_middleware(route.user_block.route_name)
def blockUser(loggedUser: LoggedUser, *args, **kwargs):
    sessionUserID = loggedUser.userID
    userID = kwargs.get("userID")
    if not userID or not isinstance(userID, int):
        return make_response({"error": f"Invalid userID {userID} dataype"}, 400)
    return _blockUser(sessionUserID, userID)


@users_blueprint.route(
    f"{route.user_unblock.route_name}/<int:userID>", methods=route.user_unblock.methods
)
@verify_request_middleware(route.user_unblock.route_name)
def unblockUser(loggedUser: LoggedUser, *args, **kwargs):
    sessionUserID = loggedUser.userID
    userID = kwargs.get("userID")
    if not userID or not isinstance(userID, int):
        return make_response({"error": f"Invalid userID {userID} dataype"}, 400)
    return _unblockUser(sessionUserID, userID)


@users_blueprint.route(
    f"{route.user_report_users.route_name}/<int:userID>",
    methods=route.user_report_users.methods,
)
@verify_request_middleware(route.user_report_users.route_name)
def reportUser(loggedUser: LoggedUser, *args, **kwargs):
    sessionUserID = loggedUser.userID
    userID = kwargs.get("userID")
    if not userID or not isinstance(userID, int):
        return make_response({"error": f"Invalid userID {userID} dataype"}, 400)
    reason = request.get_json().get("reason")
    return _reportUser(sessionUserID, userID, reason or "")
