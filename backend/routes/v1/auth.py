from config import API_ENDPOINTS, ROLE
from middlewares.verify_client_request import verify_request_middleware
from models import AccountStatus
from modules import (
    ACCESS_TOKEN_EXPIRY_MINUTES,
    HTTP_ONLY,
    REFRESH_TOKEN_EXPIRY_MINUTES,
    SECURE_COOKIE,
    Blueprint,
    json,
    make_response,
    request,
)
from repository.auth_repository import (
    _generate_otp_for_user,
    _login_user,
    _logout,
    _refresh_tokens,
    _signup_user,
    _verify_user,
)
from repository.user_repository import _get_user_profile
from utils import BadRequestError, InternalServerError, LoggedUser, UnAuthorizedError

auth_blueprint = Blueprint("auth", __name__)
"""
url_prefix causing confilct
auth_blueprint = Blueprint(
    "auth",
    __name__,
    url_prefix = 'auth'
)
"""

route = API_ENDPOINTS()


# auth/signup
@auth_blueprint.route(route.auth_signup.route_name, methods=route.auth_signup.methods)
def signup():
    body = request.get_json()
    if isinstance(body, dict):
        name = body.get("name")
        username = body.get("username")
        email = body.get("email")
        password1 = body.get("password_1")
        password2 = body.get("password_2")
        country = body.get("country") if None else "world"

        if not (username or email or password1 or password2):
            return make_response(
                {"error": "username, email and password are required"}, 400
            )
        if password1 != password2:
            return make_response({"error": "Passwords do not match"}, 400)

        return _signup_user(
            name=name,
            username=username,
            email=email,
            password=password1,
            role=ROLE.USER,  # Defualt role,
            account_status=AccountStatus.active,
            country=country,
        )
    else:
        return make_response({"error": "Expect json body"}, 401)


# /auth/login
@auth_blueprint.route(route.auth_login.route_name, methods=route.auth_login.methods)
def login():
    body = request.get_json()
    if not isinstance(body, dict):
        raise BadRequestError("Expect json body")

    username = body.get("username")
    email = body.get("email")
    password = body.get("password")
    if not (username or email):
        raise BadRequestError("Username or email is required")
    if not password:
        raise BadRequestError("Password is required")

    return _login_user(username=username, email=email, password=password)


# "/auth/logout"
@auth_blueprint.route(route.auth_logout.route_name, methods=route.auth_logout.methods)
@verify_request_middleware(route.auth_logout.route_name)
def logout(logged_user: LoggedUser, *args, **kwargs):
    refresh_token = logged_user.kwargs.get("refresh-token")
    if not refresh_token:
        return make_response({"error": "refresh token is required"}, 401)
    session_user_id = logged_user.user_id
    all_devices = str(request.args.get("all_devices", False)).lower() == "true"
    _logout(refresh_token, session_user_id, all_devices)

    res = make_response({"message": "Logged out successfully"}, 200)
    res.delete_cookie(
        key="access-token",
    )
    res.delete_cookie(
        key="refresh-token",
    )
    return res


# /auth/refresh
@auth_blueprint.route(route.auth_refresh.route_name, methods=route.auth_refresh.methods)
def refresh_token():
    # for web
    refresh_token = request.cookies.get("refresh-token") or request.headers.get(
        "refresh-token", None
    )
    if not refresh_token:
        return make_response({"error": "Refresh token is required"}, 401)

    # verify refresh token
    try:
        return _refresh_tokens(refresh_token)
    except Exception as e:
        return make_response({"error": str(e)}, 401)


#
@auth_blueprint.route(
    route.auth_generate_otp.route_name, methods=route.auth_generate_otp.methods
)
def generate_otp():
    body = request.get_json()
    user_id = body.get("user_id")
    return _generate_otp_for_user(user_id)


@auth_blueprint.route(
    route.auth_verify_otp.route_name,
    methods=route.auth_verify_otp.methods,
)
def verify():
    body = request.get_json()
    user_id = body.get("user_id")
    otp = body.get("otp")
    return _verify_user(user_id, otp)


# /auth/c/user sessionUser only
@auth_blueprint.route(
    f"{route.auth_current_user.route_name}", methods=route.auth_current_user.methods
)
@verify_request_middleware(route.auth_current_user.route_name)
def userSessionInfo(logged_user: LoggedUser, *args, **kwargs):
    try:
        user_id = logged_user.user_id
        return _get_user_profile(
            _user_id=user_id,
        )
    except Exception as e:
        return make_response({"error": str(e)}, 500)
