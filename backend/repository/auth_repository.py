from database import engine, redis_client
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
    make_response,
    or_,
    os,
    select,
    sessionmaker,
    update,
    url_for,
)
from services.mail_service import send_otp
from utils import (
    BadRequestError,
    InternalServerError,
    LoggedUser,
    ResourceNotFoundError,
    SuccessResponse,
    decode_jwt_token,
    delete_media,
    generate_jwt_token,
    generate_otp,
    match_password,
    return_hashed_bytes,
)

Session = sessionmaker(bind=engine)
session = Session()


def _signup_user(
    name: str,
    username: str,
    email: str,
    password: str,
    role: int,
    account_status: AccountStatus,
    country,
):
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
        # Close the session
        session.close()
        user_obj = {
            "id": new_user.id,
            "name": new_user.name,
            "username": new_user.username,
            "email": new_user.email,
            "join_date": new_user.created_at,
            "role": new_user.role,
            "account_status": new_user.account_status.value,
        }

        return SuccessResponse(
            data=user_obj, status_code=201, message="User created successfully"
        )
    except Exception as e:
        session.rollback()
        raise InternalServerError(str(e))


def _generate_otp_for_user(user_id: int):
    # TODO: Implement rate limiting, and check email bounce
    try:
        user = session.query(Users).filter(Users.id == user_id).first()
        if not user:
            return make_response({"error": "User not found"}, 404)
        if user.is_verified:
            return make_response({"message": "User already verified"}, 400)
        otp = generate_otp()
        redis_client.set(f"otp:{user_id}", otp, ex=600)
        send_otp(user.email, str(otp))
        session.close()
        return make_response({"message": "OTP generated successfully"}, 200)

    except Exception as e:
        print(e)
        return make_response({"error": "Internal server error"}, 500)


def _verify_user(user_id: int, entered_otp: str):
    # TODO: check user's verification state then allow for login
    try:
        user = session.query(Users).filter(Users.id == user_id).first()
        if not user:
            return make_response({"error": "User not found"}, 404)
        if user.is_verified:
            return make_response({"message": "User already verified"}, 400)

        stored_otp = redis_client.get(f"otp:{user_id}")
        if not stored_otp:
            return make_response({"error": "OTP expired"}, 400)
        if stored_otp != entered_otp:
            return make_response({"error": "Invalid OTP"}, 400)

        user.is_verified = True
        session.commit()
        session.refresh(user)
        session.close()
        return make_response({"message": "OTP verified successfully"}, 200)
    except Exception as e:
        print(e)
        return make_response({"error": "Internal server error"}, 500)


def _login_user(username, email, password):
    """
    Check user's account status ["active", "suspended", "banned", "deleted"]
    """
    try:
        # Query the user
        users = (
            session.query(Users)
            .where(or_(Users.email == email, Users.username == username))
            .first()
        )
        session.close()
        if not users:
            return make_response({"message": "user does not exist"}, 404)
        if users.account_status == AccountStatus.suspended:
            return make_response({"message": "user is suspended"}, 403)
        if users.account_status == AccountStatus.banned:
            return make_response({"message": "user is banned"}, 403)
        if users.account_status == AccountStatus.deleted:
            return make_response({"message": "user is deleted"}, 403)
        if not match_password(password.encode("ascii"), users.password):
            return make_response({"error": "Invalid password"}, 401)
        access_obj = {
            "id": users.id,
            "name": users.name,
            "username": users.username,
            "email": users.email,
            "join_date": users.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "role": users.role,
            "account_status": users.account_status.value,
        }
        refresh_obj = {
            "id": users.id,
            "name": users.name,
            "username": users.username,
        }

        access_token = generate_jwt_token(
            user_data=access_obj, expire_in_minute=ACCESS_TOKEN_EXPIRY_MINUTES
        )
        refresh_token = generate_jwt_token(
            user_data=refresh_obj, expire_in_minute=REFRESH_TOKEN_EXPIRY_MINUTES
        )

        stmt = Sessions(user_id=users.id, refreshtoken=refresh_token)
        session.add(stmt)
        session.commit()
        # Close the session
        session.close()

        res = make_response(
            {
                "message": "Logged in successfully",
                "data": {"user_id": users.id, "username": users.username},
            },
            200,
        )
        res.set_cookie(
            key="access-token",
            value=access_token,
            httponly=HTTP_ONLY,
            secure=SECURE_COOKIE,
            max_age=ACCESS_TOKEN_EXPIRY_MINUTES * 60,
        )
        res.set_cookie(
            key="refresh-token",
            value=refresh_token,
            httponly=HTTP_ONLY,
            secure=SECURE_COOKIE,
            samesite=None,
            max_age=REFRESH_TOKEN_EXPIRY_MINUTES * 60,
        )
        return res

    except Exception as e:
        session.rollback()
        print("hii")
        raise InternalServerError(str(e)) from e


def _refresh_tokens(refresh_token: str):
    try:
        decoded_data = decode_jwt_token(refresh_token)
        if not decoded_data:
            raise Exception("Token expired")
        user_id = decoded_data["data"]["id"]
        # TODO: check account status too
        # if accountStatus == "active":
        #     pass
        stmt = (
            select(Users, Sessions.refresh_token)
            .join_from(Users, Sessions)
            .where(Sessions.refresh_token == refresh_token)
        )
        user_result = session.execute(stmt).first()
        session.close()
        if not user_result or refresh_token != user_result[1]:
            return make_response({"error": "Invalid refresh token"}, 401)
        # Delete previous refresh token of user
        stmt = (
            update(Sessions)
            .where(Sessions.refresh_token == refresh_token)
            .values(refresh_token="")
        )
        session.execute(stmt)
        session.commit()
        session.close()

        user: Users = user_result[0]

        new_access_token = generate_jwt_token(
            user_data={
                "id": user.id,
                "name": user.name,
                "username": user.username,
                "email": user.email,
                "join_date": user.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                "role": user.role,
                "account_status": user.account_status.value,
            },
            expire_in_minute=ACCESS_TOKEN_EXPIRY_MINUTES,
        )
        new_refresh_token = generate_jwt_token(
            user_data={
                "id": user.id,
                "name": user.name,
                "username": user.username,
            },
            expire_in_minute=REFRESH_TOKEN_EXPIRY_MINUTES,
        )
        session.close()
        stmt = Sessions(user_id=user.id, refresh_token=new_refresh_token)
        session.add(stmt)
        session.commit()
        session.close()

        res = make_response(
            {
                "message": "Token refreshed successfully",
                "data": {"user_id": user.id, "username": user.username},
            },
            200,
        )
        res.set_cookie(
            key="access_token",
            value=new_access_token,
            httponly=HTTP_ONLY,
            secure=SECURE_COOKIE,
            max_age=ACCESS_TOKEN_EXPIRY_MINUTES * 60,
        )
        res.set_cookie(
            key="refresh_token",
            value=new_refresh_token,
            httponly=HTTP_ONLY,
            secure=SECURE_COOKIE,
            samesite=None,
            max_age=REFRESH_TOKEN_EXPIRY_MINUTES * 60,
        )
        return res
    except Exception as e:
        session.rollback()
        print(e)
        raise Exception(e)


def _logout(refresh_token: str, user_id: int, all_devices=False):
    try:
        user = None
        if all_devices:
            user = session.query(Sessions).filter_by(user_id=user_id).first()
        else:
            user = (
                session.query(Sessions).filter_by(refresh_token=refresh_token).first()
            )

        if not user:
            raise Exception("User session not found")
        if all_devices:
            stmt = delete(Sessions).where(Sessions.user_id == user_id)
            session.execute(stmt)
            session.commit()
            session.close()
        else:
            stmt = delete(Sessions).filter_by(refresh_token=refresh_token)
            session.execute(stmt)
            session.commit()
            session.close()
    except Exception as e:
        raise Exception(e)
