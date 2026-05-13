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
from repository.user_respository import (
    _authenticateUser,
    _createUser,
    _generateOTPforUser,
    _logout,
    _refreshTokens,
    _verifyUser,
)
from utils import LoggedUser

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
@auth_blueprint.route(route.signupUser.routeName, methods=route.signupUser.methods)
def signup():
    clientBody = request.get_json()
    if isinstance(clientBody, dict):
        name = clientBody.get("name")
        userName = clientBody.get("userName")
        email = clientBody.get("email")
        password1 = clientBody.get("password1")
        password2 = clientBody.get("password2")
        country = clientBody.get("country") if None else "world"

        if not (userName or email or password1 or password2):
            return make_response(
                {"error": "userName, email and password are required"}, 400
            )
        if password1 != password2:
            return make_response({"error": "Passwords do not match"}, 400)

        return _createUser(
            name=name,
            userName=userName,
            email=email,
            password=password1,
            role=ROLE.USER,  # Defualt role,
            accountStatus=AccountStatus.active,
            country=country,
        )
    else:
        return make_response({"error": "Expect json body"}, 401)


# /auth/login
@auth_blueprint.route(route.loginUser.routeName, methods=route.loginUser.methods)
def login():
    try:
        clientBody = request.get_json()
        if isinstance(clientBody, dict):
            userName = clientBody.get("userName")
            email = clientBody.get("email")
            password = clientBody.get("password")
            if not (userName or email):
                return make_response({"error": "Username or email is required"}, 400)
            if not password:
                return make_response({"error": "Password is required"}, 400)

            return _authenticateUser(userName=userName, email=email, password=password)
        else:
            return make_response({"error": "Expect json body"}, 401)
    except Exception as e:
        return make_response({"error": str(e)}, 500)


# "/auth/logout"
@auth_blueprint.route(route.logoutUser.routeName, methods=route.logoutUser.methods)
@verify_request_middleware(route.logoutUser.routeName)
def logout(loggedUser: LoggedUser, *args, **kwargs):
    refreshToken = loggedUser.kwargs.get("refreshToken")
    if not refreshToken:
        return make_response({"error": "refresh token is required"}, 401)
    sessionUserID = loggedUser.userID
    allDevices = str(request.args.get("allDevices", False)).lower() == "true"
    _logout(refreshToken, sessionUserID, allDevices)

    res = make_response({"message": "Logged out successfully"}, 200)
    res.delete_cookie(
        key="accessToken",
    )
    res.delete_cookie(
        key="refreshToken",
    )
    return res


# /auth/refresh
@auth_blueprint.route(route.refreshToken.routeName, methods=route.refreshToken.methods)
def refreshToken():
    # for web
    refreshToken = request.cookies.get("refreshToken") or request.headers.get(
        "refreshToken", None
    )
    if not refreshToken:
        return make_response({"error": "Refresh token is required"}, 401)

    # verify refresh token
    try:
        return _refreshTokens(refreshToken)
    except Exception as e:
        return make_response({"error": str(e)}, 401)


@auth_blueprint.route(
    f"{route.genrateOtp.routeName}/<int:userID>", methods=route.genrateOtp.methods
)
def generateOTP(userID):
    return _generateOTPforUser(userID)


@auth_blueprint.route(
    f"{route.verifyUser.routeName}/<int:userID>/<string:otp>",
    methods=route.verifyUser.methods,
)
def verify(userID, otp):
    return _verifyUser(userID, otp)


# /auth/c/user sessionUser only
@usersBlueprint.route(
    f"{route.auth_current_user.route_name}", methods=route.auth_current_user.methods
)
@verify_request_middleware(route.auth_current_user.route_name)
def userSessionInfo(loggedUser: LoggedUser, *args, **kwargs):
    try:
        userID = loggedUser.user_id
        return getUserProfile(
            _userID=userID,
        )
    except Exception as e:
        return make_response({"error": str(e)}, 500)
