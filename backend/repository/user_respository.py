from database import engine, redis_client
from models import (
    AccountStatus,
    BlockedUsers,
    Follower,
    Profile,
    ReportedUsers,
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
    IndternalServerError,
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
from werkzeug.exceptions import InternalServerError

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
        raise IndternalServerError(str(e))


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
        print(e)
        raise Exception(e)


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


def _add_follower(session_user_id: int, user_id: int):
    try:
        is_already_follow = select(
            exists().where(
                Follower.user_id == user_id, Follower.follower_id == session_user_id
            )
        )
        is_already_follow = session.scalar(
            is_already_follow
        )  # Scalar select first row from table
        session.close()
        # If is_already_follow
        if not is_already_follow:
            new_follower = Follower(user_id=user_id, follower_id=session_user_id)
            session.add(new_follower)
            session.commit()
            session.close()
            return make_response(
                {"message": "follower added successfully", "isFollowing": True}, 201
            )
        else:
            return make_response({"error": "user already follows requested user"}, 409)
    except Exception as e:
        session.rollback()
        print(e)
        return make_response({"error": f"{e}"}, 500)


def _remove_follower(
    session_user_id: int,
    user_id: int,
    user_remove_follower: bool = False,  # User wants to remove his follower itself
):
    """
    Follower can unfollow user
    User can remove another user from following list
    """
    try:
        if user_remove_follower:
            is_already_follow = select(
                exists().where(
                    Follower.user_id == session_user_id, Follower.follower_id == user_id
                )
            )
        else:
            is_already_follow = select(
                exists().where(
                    Follower.user_id == user_id, Follower.follower_id == session_user_id
                )
            )

        is_already_follow = session.scalar(
            is_already_follow
        )  # Scalar select first row from table

        session.close()
        # If is_already_follow
        if not is_already_follow:
            return make_response({"error": "User is not following requested user"}, 409)

        if user_remove_follower:
            stmt = delete(Follower).where(
                Follower.user_id == session_user_id, Follower.follower_id == user_id
            )
        else:
            stmt = delete(Follower).where(
                Follower.user_id == user_id, Follower.follower_id == session_user_id
            )
        session.execute(stmt)
        session.commit()
        return make_response(
            {"message": "user unfollows requested user", "isFollowing": False}, 200
        )
    except Exception as e:
        print(e)
        return make_response({"error": f"{e}"}, 500)


def _get_user_profile(
    _username: str | None = None,
    _email: str | None = None,
    _user_id: int | None = None,
    session_user_id: int | None = None,
):
    """
    Retrieve a user profile based on the input parameters: username, email, or uid. Only
    one field should be provided to successfully query a user. If no valid argument
    is passed, an error response is returned. The function queries the database, closes
    the session afterward, and fetches details of the user(s). If a user exists, their
    profile details are returned in the response payload; otherwise, an error message
    is provided.

    :param _username: Username of the user to be queried
    :param _email: Email address of the user to be queried
    :param _user_id: Unique identifier of the user to be queried
    :return: JSON response containing the user's data if the user exists or an error
             message
    """

    try:
        # User's follower count
        follower_count = aliased(Follower)
        # User's following count
        following_count = aliased(Follower)

        match_by = {}
        if _user_id:
            match_by["id"] = _user_id
        elif _username:
            match_by["username"] = _username
        elif _email:
            match_by["email"] = _email
        if len(match_by) == 0:
            raise ValueError("No match criteria provided")
        # Query the user
        stmt = (
            select(
                Users,
                Profile.bio,
                Profile.country,
                Profile.media_url,
                Profile.media_public_id,
                Profile.file_extension,
                func.count(follower_count.user_id).label("follower_count"),
                func.count(following_count.follower_id).label("following_count"),
                exists(
                    select(Follower).where(Follower.follower_id == session_user_id)
                ).label(
                    "is_following"  # Whether session user follows or not
                ),
            )
            .select_from(Users)
            .filter_by(**match_by)  # Apply matches to User only while in context
            .outerjoin(follower_count, follower_count.user_id == Users.id)
            .outerjoin(following_count, following_count.follower_id == Users.id)
            .outerjoin(Profile, Profile.user_id == Users.id)
            .group_by(Users.id, Profile.id)
        )
        users = session.execute(stmt).all()
        # Close the session
        session.close()
        if users:
            usersDict = [
                {
                    "id": user[0].id,
                    "name": user[0].name,
                    "username": user[0].userName,
                    "email": user[0].email if session_user_id == user[0].id else "",
                    "join_date": user[0].createdAt.strftime("%Y-%m-%d %H:%M:%S"),
                    "role": user[0].role,
                    "account_status": user[0].accountStatus.value,
                    "bio": user[1],
                    "country": user[2],
                    "profile_img_url": user[3]
                    if USE_CLOUDINARY_STORAGE
                    else f"{API_ROOT_URL}{url_for('profileImage.serveImage', fileName=f'{user[4]}.{user[5]}')}",
                    "follower_count": user[6],
                    "following_count": user[7],
                    "is_following": user[8],
                }
                for user in users
            ]
            return SuccessResponse(
                data=usersDict[0], message="Fetched user detail successfully"
            )
        else:
            raise ResourceNotFoundError("User does not exist")
    except Exception as e:
        raise IndternalServerError("Error while fetching user profile " + str(e))


def _update_profile_img(
    session_user_id: int,
    media_public_id: str,
    file_extension: str,
    file_type: str,
    media_url: str | None = None,
):
    try:
        user_profile = (
            session.query(Profile).where(Profile.user_id == session_user_id).first()
        )
        session.close()
        if not user_profile:
            return make_response({"message": "user does not exist"}, 404)

        # Delete previous profile image if exists
        if user_profile.media_public_id:
            if USE_CLOUDINARY_STORAGE:
                delete_media([user_profile.media_public_id])
            else:
                filepath = os.path.join(
                    PUBLIC_DIRECTORY_PROFILES,
                    f"{user_profile.media_public_id}.{user_profile.fileType}",
                )
                if os.path.exists(filepath):
                    os.remove(filepath)

        stmt = (
            update(Profile)
            .where(Profile.user_id == session_user_id)
            .values(
                media_public_id=media_public_id,
                file_extension=file_extension,
                file_type=file_type,
                media_url=media_url,
            )
        )
        session.execute(stmt)
        session.commit()
        session.close()
        return make_response({"message": "profile image updated successfully"}, 201)
    except Exception as e:
        print(f"Error updating profile image: {e}")
        return make_response({"error": f"{e}"}, 500)


def _update_user(
    session_user_id: int,
    name: str | None,
    bio: str | None,
    age: int | None,
    country: str | None,
):
    try:
        user = session.query(Users).where(Users.id == session_user_id).first()
        if not user:
            return make_response({"message": "user does not exist"}, 404)

        if name:
            # Update the name
            user.name = name
            session.commit()
            session.close()
        update_obj = {}
        if bio:
            update_obj["bio"] = bio
        if age:
            update_obj["age"] = age
        if country:
            update_obj["country"] = country

        if len(update_obj) > 0:
            stmt = (
                update(Profile)
                .where(Profile.user_id == session_user_id)
                .values(**update_obj)
            )
            session.execute(stmt)
            session.commit()
            session.close()
        return make_response({"message": "user updated successfully"}, 201)
    except Exception as e:
        print(f"Error updating user: {e}")
        return make_response({"message": "failed to update user"}, 500)


def _block_user(session_user_id: int, user_id: int):
    try:
        # Check has user already blocked or not
        stmt = select(
            exists().where(
                BlockedUsers.blocked_by == session_user_id,
                BlockedUsers.user_id == user_id,
            )
        )
        user = session.scalar(stmt)
        session.close()
        if not user:
            blocked_user = BlockedUsers(user_id=user_id, blocked_by=session_user_id)
            session.add(blocke_user)
            session.commit()
            session.close()
            return make_response(
                {"message": "User blocked successfully", "isBlocked": True}, 201
            )

        return make_response(
            {"error": "User is already blocked", "isBlocked": True}, 409
        )
    except Exception as e:
        session.rollback()
        session.close()
        print(e)
        return make_response({"error": f"{e}"}, 500)


def _unblock_user(session_user_id: int, user_id: int):
    try:
        # Check has user already blocked or not
        stmt = select(
            exists().where(
                BlockedUsers.blocked_by == session_user_id,
                BlockedUsers.user_id == user_id,
            )
        )
        user = session.scalar(stmt)
        session.close()
        # Remove the user from the table
        if user:
            stmt = delete(BlockedUsers).where(
                BlockedUsers.blocked_by == session_user_id,
                BlockedUsers.user_id == user_id,
            )
            session.execute(stmt)
            session.commit()
            session.close()
            return make_response(
                {"message": "User unblocked successfully", "isBlocked": False}, 201
            )

        return make_response(
            {"error": "User has already unblocked the person", "isBlocked": False}, 409
        )
    except Exception as e:
        session.rollback()
        session.close()
        print(e)
        return make_response({"error": f"{e}"}, 500)


def _report_user(session_user_id: int, user_id: int, reason: str):
    try:
        stmt = ReportedUsers(
            reportedBy=session_user_id, user_id=user_id, description=reason
        )
        session.add(stmt)
        session.commit()
        session.close()
        return make_response({"message": "User reported successfully"}, 201)
    except Exception as e:
        session.rollback()
        session.close()
        print(e)
        return make_response({"error": f"{e}"}, 500)
