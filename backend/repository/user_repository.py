from database import SessionLocal, redis_client
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
    request,
    select,
    sessionmaker,
    update,
    url_for,
)
from services.cloudinary_service import delete_media
from services.mail_service import send_otp
from utils import (
    AppError,
    BadRequestError,
    ConflictError,
    InternalServerError,
    LoggedUser,
    ResourceNotFoundError,
    SuccessResponse,
    decode_jwt_token,
    generate_jwt_token,
    generate_otp,
    match_password,
    return_hashed_bytes,
)


def _add_follower(session_user_id: int, user_id: int):
    session = SessionLocal()
    try:
        is_already_follow = select(
            exists().where(
                Follower.user_id == user_id, Follower.follower_id == session_user_id
            )
        )
        is_already_follow = session.scalar(
            is_already_follow
        )  # Scalar select first row from table

        # If is_already_follow
        if not is_already_follow:
            new_follower = Follower(user_id=user_id, follower_id=session_user_id)
            session.add(new_follower)
            session.commit()

            return SuccessResponse(
                data={"is_following": True},
                message="follower added successfully",
                status_code=201,
            )
        else:
            raise ConflictError("User already follows requested user")
    except AppError:
        session.rollback()
        raise
    except Exception as e:
        session.rollback()
        raise InternalServerError("Error while following user") from e
    finally:
        session.close()


def _remove_follower(
    session_user_id: int,
    user_id: int,
    user_remove_follower: bool = False,  # User wants to remove his follower itself
):
    """
    Follower can unfollow user
    User can remove another user from following list
    """
    session = SessionLocal()
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

        # If is_already_follow
        if not is_already_follow:
            raise ConflictError("User is not following requested user")

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
        return SuccessResponse(
            data={"is_following": False},
            status_code=201,
            message="user unfollows requested user",
        )
    except AppError:
        raise
    except Exception as e:
        raise InternalServerError("Error while unfollowing user") from e
    finally:
        session.close()


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

    session = SessionLocal()
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

        if users:
            usersDict = [
                {
                    "user_id": user[0].id,
                    "name": user[0].name,
                    "username": user[0].username,
                    "email": user[0].email if session_user_id == user[0].id else "",
                    "join_date": user[0].created_at.strftime("%Y-%m-%d %H:%M:%S"),
                    "role": user[0].role,
                    "account_status": user[0].account_status.value,
                    "bio": user[1],
                    "country": user[2],
                    "profile_img_url": user[3]
                    if USE_CLOUDINARY_STORAGE
                    else f"{API_ROOT_URL or request.host_url}{url_for('return_assets.serve_image', filename=f'{user[4]}.{user[5]}')}",
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

    except AppError:
        raise
    except Exception as e:
        raise InternalServerError("Error while fetching user profile " + str(e))
    finally:
        session.close()


def _update_profile_img(
    session_user_id: int,
    media_public_id: str,
    file_extension: str,
    file_type: str,
    media_url: str | None = None,
):
    session = SessionLocal()
    try:
        user_profile = (
            session.query(Profile).where(Profile.user_id == session_user_id).first()
        )

        if not user_profile:
            raise ResourceNotFoundError("User not found")

        # Delete previous profile image if exists
        if user_profile.media_public_id:
            if USE_CLOUDINARY_STORAGE:
                delete_media([user_profile.media_public_id])
            else:
                filepath = os.path.join(
                    PUBLIC_DIRECTORY_PROFILES,
                    f"{user_profile.media_public_id}.{user_profile.file_type}",
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

        return SuccessResponse(
            message="profile image updated successfully", status_code=201, data={}
        )

    except AppError:
        raise
    except Exception as e:
        raise InternalServerError("Error while update profile image") from e
    finally:
        session.close()


def _update_user(
    session_user_id: int,
    name: str | None,
    bio: str | None,
    age: int | None,
    country: str | None,
):
    session = SessionLocal()
    try:
        user = session.query(Users).where(Users.id == session_user_id).first()
        if not user:
            raise ResourceNotFoundError("User does not exist")

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

        return SuccessResponse(
            message="user updated successfully", status_code=201, data={}
        )
    except AppError:
        raise
    except Exception as e:
        raise InternalServerError("Error while updating user profile") from e
    finally:
        session.close()


def _block_user(session_user_id: int, user_id: int):
    session = SessionLocal()
    try:
        # Check has user already blocked or not
        stmt = select(
            exists().where(
                BlockedUsers.blocked_by == session_user_id,
                BlockedUsers.user_id == user_id,
            )
        )
        user = session.scalar(stmt)

        if not user:
            blocked_user = BlockedUsers(user_id=user_id, blocked_by=session_user_id)
            session.add(blocked_user)
            session.commit()

            return SuccessResponse(
                message="User blocked successfully",
                data={"is_blocked": True},
                status_code=201,
            )

        raise ConflictError("User is already blocked")
    except AppError:
        raise
    except Exception as e:
        session.rollback()
        raise InternalServerError("Error while blocking user") from e
    finally:
        session.close()


def _unblock_user(session_user_id: int, user_id: int):
    session = SessionLocal()
    try:
        # Check has user already blocked or not
        stmt = select(
            exists().where(
                BlockedUsers.blocked_by == session_user_id,
                BlockedUsers.user_id == user_id,
            )
        )
        user = session.scalar(stmt)

        # Remove the user from the table
        if user:
            stmt = delete(BlockedUsers).where(
                BlockedUsers.blocked_by == session_user_id,
                BlockedUsers.user_id == user_id,
            )
            session.execute(stmt)
            session.commit()

            return SuccessResponse(
                message="User unblocked successfully",
                data={"is_blocked": False},
                status_code=200,
            )

        raise ConflictError("User has already unblocked the person")
    except AppError:
        session.rollback()
        raise
    except Exception as e:
        session.rollback()
        raise InternalServerError("Error while unblocking user") from e
    finally:
        session.close()


def _report_user(session_user_id: int, user_id: int, reason: str):
    session = SessionLocal()
    try:
        stmt = ReportedUsers(
            reported_by=session_user_id, user_id=user_id, description=reason
        )
        session.add(stmt)
        session.commit()
        return SuccessResponse(
            message="User reported successfully", data={}, status_code=201
        )
    except AppError:
        session.rollback()
        raise
    except Exception as e:
        session.rollback()
        raise InternalServerError("Error while reporting user") from e
    finally:
        session.close()
