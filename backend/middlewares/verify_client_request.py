from config import API_ENDPOINTS, ROLE
from modules import functools, make_response, re, request
from repository.check_user_role import get_user_role
from utils import LoggedUser, decode_jwt_token

apiEndpointsPartialAccess = API_ENDPOINTS().api_endpoints_partial_access


def verify_request_middleware(endpoint: str):
    # below decorator
    def verify_client_request(func):
        @functools.wraps(func)
        def check_client_request(*args, **kwargs):
            # before main function runs
            access_token = None
            authorization = request.headers.get("authorization")
            refresh_token = request.headers.get("refresh_token")
            # Check request medium if mobile
            if authorization is not None and re.match(
                "^Bearer *([^ ]+)", authorization, flags=0
            ):
                access_token = authorization.split(" ")[1]
            else:
                # Check of web
                access_token = request.cookies.get("access_token")
                refresh_token = request.cookies.get("refresh_token")

            if access_token:
                try:
                    decoded_token = decode_jwt_token(access_token)
                    if decoded_token:
                        # Match the user id and role for this endpoint
                        result = get_user_role(
                            endpoint, decoded_token["payload"]["role"]
                        )
                        if result:
                            return func(
                                logge_user=LoggedUser(
                                    user_id=decoded_token["payload"]["id"],
                                    role_id=decoded_token["payload"]["role"],
                                    role_name=ROLE().rolesIds[
                                        decoded_token["payload"]["role"]
                                    ],
                                    access_token=access_token,
                                    refresh_token=refresh_token,
                                ),
                                *args,
                                **kwargs,
                            )
                        else:
                            # Either user role or endpoint not found
                            return make_response(
                                {"message": "Invalid user role or route"}, 401
                            )

                    else:
                        return make_response({"error": "Token expired"}, 401)
                except Exception as e:
                    return make_response(
                        {"error": f"{e}", "message": "Provide valid token"}, 401
                    )

            elif apiEndpointsPartialAccess.get(endpoint):
                # Give user partial access
                return func(
                    loggedUser=None,
                    *args,
                    **kwargs,
                )
            else:
                return make_response(
                    {"error": "Invalid token", "message": "No auth token found"}, 401
                )

            # after main function run

        # Renaming the function name:
        # checkClientRequest.__name__ = func.__name__
        return check_client_request

    return verify_client_request
