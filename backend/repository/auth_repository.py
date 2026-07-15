from database import SessionLocal, redis_client
from models import (
    AccountStatus,
    Profile,
    Sessions,
    Users,
)
from modules import (
    ACCESS_TOKEN_EXPIRY_MINUTES,
    API_ROOT_URL,
    HTTP_ONLY,
    PUBLIC_DIRECTORY_PROFILES,
    REFRESH_TOKEN_EXPIRY_MINUTES,
    SECURE_COOKIE,
    USE_CLOUDINARY_STORAGE,
    USE_EMAIL_SERVICE,
    aliased,
    delete,
    exists,
    func,
    jsonify,
    jwt,
    make_response,
    or_,
    os,
    request,
    select,
    sessionmaker,
    update,
)
from services.cloudinary_service import delete_media
from services.mail_service import send_otp
from utils import (
    AccessRefreshTokens,
    AppError,
    BadRequestError,
    ForbiddenError,
    InternalServerError,
    InvalidCredentialsError,
    RateLimitExceededError,
    ResourceNotFoundError,
    SuccessResponse,
    TokenExpiredError,
    decode_jwt_token,
    generate_jwt_token,
    generate_otp,
    match_password,
    return_hashed_bytes,
)


def _generate_access_and_refresh_token(user: Users, message: str) -> SuccessResponse:

    client_type = request.headers.get("x-client-type")
    if not client_type or client_type not in ["web", "mobile"]:
        raise InvalidCredentialsError("Invalid client type")
    session = SessionLocal()
    access_obj = {
        "id": user.id,
        "name": user.name,
        "username": user.username,
        "email": user.email,
        "join_date": user.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        "role": user.role,
        "account_status": user.account_status.value,
    }
    refresh_obj = {
        "id": user.id,
        "name": user.name,
        "username": user.username,
    }

    access_token = generate_jwt_token(
        user_data=access_obj, expire_in_minute=ACCESS_TOKEN_EXPIRY_MINUTES
    )
    refresh_token = generate_jwt_token(
        user_data=refresh_obj, expire_in_minute=REFRESH_TOKEN_EXPIRY_MINUTES
    )
    try:
        stmt = Sessions(user_id=user.id, refresh_token=refresh_token)
        session.add(stmt)
        session.commit()
    except Exception as e:
        session.rollback()
        raise InternalServerError(str(e)) from e
    finally:
        # Close the session
        session.close()

    payload = {"user_id": user.id, "username": user.username}
    if client_type == "mobile":
        payload["access_token"] = access_token
        payload["refresh_token"] = refresh_token
    res = SuccessResponse(
        data=payload,
        status_code=200,
        message=message,
    )
    if client_type == "web":
        res.set_cookie(
            key="access-token",
            value=access_token,
            httponly=HTTP_ONLY,
            secure=SECURE_COOKIE,
            path="/",
            samesite="None",
            max_age=ACCESS_TOKEN_EXPIRY_MINUTES * 60,
        )
        res.set_cookie(
            key="refresh-token",
            value=refresh_token,
            httponly=HTTP_ONLY,
            secure=SECURE_COOKIE,
            path="/",
            samesite="None",
            max_age=REFRESH_TOKEN_EXPIRY_MINUTES * 60,
        )
    return res


def _signup_user(
    name: str,
    username: str,
    email: str,
    password: str,
    role: int,
    account_status: AccountStatus,
    country: str,
):
    session = SessionLocal()
    try:
        # Check if user already exist
        user = (
            session.query(Users)
            .filter(or_(Users.username == username, Users.email == email))
            .first()
        )
        if user:
            raise BadRequestError("User already exists")
        # Add a user
        new_user = Users(
            name=name,
            username=username,
            email=email,
            password=return_hashed_bytes(password.encode("ascii")),
            role=role,
            account_status=account_status,
            profile=Profile(country=country),
        )
        session.add(new_user)
        session.commit()
        session.refresh(new_user)
        user_obj = {
            "id": new_user.id,
            "name": new_user.name,
            "username": new_user.username,
            "email": new_user.email,
            "join_date": new_user.created_at.isoformat(),
            "role": new_user.role,
            "account_status": new_user.account_status.value,
        }

        return SuccessResponse(
            data=user_obj, status_code=201, message="User created successfully"
        )
    except AppError:
        session.rollback()
        raise
    except Exception as e:
        session.rollback()
        # TODO: Log the exception
        raise InternalServerError("Error while creating user") from e
    finally:
        # Close the session
        session.close()


def _generate_otp_for_user(user_id: int):
    session = SessionLocal()
    # TODO: check email bounce

    key = f"rate_limit:{user_id}"

    count = redis_client.incr(key)

    if count == 1:
        redis_client.expire(key, 30)

    if count > 3:
        ttl = redis_client.ttl(key)
        raise RateLimitExceededError(
            f"Rate limit exceeded. Try again after {ttl} seconds."
        )

    try:
        user = session.query(Users).filter(Users.id == user_id).first()
        if not user:
            raise ResourceNotFoundError("User not found")
        if user.is_verified:
            raise BadRequestError("User already verified")
        otp = generate_otp()
        redis_client.set(f"otp:{user_id}", otp, ex=600)
        send_otp(user.email, str(otp))
        session.close()
        return SuccessResponse(
            data={"message": "OTP generated successfully"}, status_code=200
        )
    except AppError:
        raise
    except Exception as e:
        raise InternalServerError("Failed to generate OTP") from e


def _verify_user(user_id: int, entered_otp: str):
    session = SessionLocal()
    # TODO: check user's verification state then allow for login
    try:
        user = session.query(Users).filter(Users.id == user_id).first()
        if not user:
            raise ResourceNotFoundError("User not found")
        if user.is_verified:
            raise BadRequestError("User already verified")

        stored_otp = redis_client.get(f"otp:{user_id}")

        if not stored_otp:
            raise BadRequestError("OTP expired")
        if stored_otp != str(entered_otp):
            raise BadRequestError("Invalid OTP")

        user.is_verified = True
        session.commit()
        return SuccessResponse(
            data={"message": "OTP verified successfully"}, status_code=200
        )
    except AppError:
        session.rollback()
        raise
    except Exception as e:
        session.rollback()
        raise InternalServerError("Failed to verify OTP") from e
    finally:
        session.close()


def _login_user(username, email, password):
    """
    Check user's account status ["active", "suspended", "banned", "deleted"]
    """
    session = SessionLocal()
    # Query the user
    users = (
        session.query(Users)
        .where(or_(Users.email == email, Users.username == username))
        .first()
    )
    session.close()
    if not users:
        raise ResourceNotFoundError("User not found")
    if users.account_status == AccountStatus.suspended:
        raise ForbiddenError("User is suspended")
    if users.account_status == AccountStatus.banned:
        raise ForbiddenError("User is banned")
    if users.account_status == AccountStatus.deleted:
        raise ForbiddenError("User is deleted")
    if not match_password(password.encode("ascii"), users.password):
        raise ForbiddenError("Invalid password")

    res = _generate_access_and_refresh_token(users, "Logged in successfully")

    return res


def _refresh_tokens(refresh_token: str):
    session = SessionLocal()
    try:
        decoded_data = decode_jwt_token(refresh_token)
        if not decoded_data:
            raise TokenExpiredError("Token expired, Please login again")
        user_id = decoded_data["payload"]["id"]
        # TODO: check account status too
        # if accountStatus == "active":
        #     pass
        stmt = (
            select(Users, Sessions.refresh_token)
            .join_from(Users, Sessions)
            .where(Sessions.refresh_token == refresh_token)
        )
        user_result = session.execute(stmt).first()

        if not user_result or refresh_token != user_result[1]:
            raise TokenExpiredError("Invalid refresh token")
        # Delete previous refresh token of user
        stmt = (
            update(Sessions)
            .where(Sessions.refresh_token == refresh_token, Sessions.user_id == user_id)
            .values(refresh_token="")
        )
        session.execute(stmt)
        session.commit()

        user: Users = user_result[0]

        res = _generate_access_and_refresh_token(user, "Session successfully refreshed")

        return res
    except AppError:
        session.rollback()
        raise
    except jwt.InvalidSignatureError:
        raise TokenExpiredError("Invalid refresh token")
    except jwt.ExpiredSignatureError:
        raise TokenExpiredError("Refresh token expired")
    except Exception as e:
        session.rollback()
        raise InternalServerError("Error while refreshing session") from e
    finally:
        session.close()


def _logout(refresh_token: str, user_id: int, all_devices=False):
    session = SessionLocal()
    try:
        user = None
        if all_devices:
            user = session.query(Sessions).filter_by(user_id=user_id).first()
        else:
            user = (
                session.query(Sessions).filter_by(refresh_token=refresh_token).first()
            )
        if not user:
            raise ResourceNotFoundError("User session not found")

        # TODO: Rather than deleting all sessions rows, consider invalidating the refresh token instead
        # This will help to obtain analytics on active devices
        if all_devices:
            stmt = delete(Sessions).where(Sessions.user_id == user_id)
            session.execute(stmt)
            session.commit()

        else:
            stmt = delete(Sessions).filter_by(refresh_token=refresh_token)
            session.execute(stmt)
            session.commit()

    except AppError:
        raise

    except Exception as e:
        raise InternalServerError("Failed to logout") from e

    finally:
        # Close the session
        session.close()
