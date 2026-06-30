from config import API_ENDPOINTS, ROLE
from modules import functools, make_response, re, request
from repository.check_user_role import get_user_role
from utils import (
    AppError,
    InternalServerError,
    LoggedUser,
    UnAuthorizedError,
    decode_jwt_token,
)

apiEndpointsPartialAccess = API_ENDPOINTS().api_endpoints_partial_access


def verify_request_middleware(endpoint: str):
    # below decorator
    def verify_client_request(func):
        @functools.wraps(func)
        def check_client_request(*args, **kwargs):
            # before main function runs
            access_token = None
            authorization = request.headers.get("authorization")
            refresh_token = request.headers.get("refresh-token")
            # Check request medium if mobile
            if authorization is not None and re.match(
                "^Bearer *([^ ]+)", authorization, flags=0
            ):
                access_token = authorization.split(" ")[1]
            else:
                # Check of web
                access_token = request.cookies.get("access-token")
                refresh_token = request.cookies.get("refresh-token")

            if access_token:
                decoded_token = decode_jwt_token(access_token)
                if decoded_token:
                    user_id = decoded_token["payload"]["id"]
                    user_role = decoded_token["payload"]["role"]

                    # Match the user id and role for this endpoint
                    has_access_right = get_user_role(endpoint, user_id, user_role)

                    if has_access_right:
                        return func(
                            logged_user=LoggedUser(
                                user_id=user_id,
                                role_id=user_role,
                                role_name=ROLE().rolesIds[user_role],
                                access_token=access_token,
                                refresh_token=refresh_token,
                            ),
                            *args,
                            **kwargs,
                        )
                    else:
                        # Either user role or endpoint not found
                        raise UnAuthorizedError("Invalid user role or route")

                else:
                    raise UnAuthorizedError("Auth token expired")

            elif apiEndpointsPartialAccess.get(endpoint):
                # Give user partial access
                return func(
                    logged_user=None,
                    *args,
                    **kwargs,
                )
            else:
                raise UnAuthorizedError("No auth token found")

            # after main function run

        # Renaming the function name:
        # checkClientRequest.__name__ = func.__name__
        return check_client_request

    return verify_client_request
