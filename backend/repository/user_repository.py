from database import SessionLocal, redis_client
from models import (
    AccountStatus,
    BlockedUsers,
    Follower,
    Profile,
    ReportedUsers,
    Role,
    Sessions,
    Users,
)
from modules import (
    PUBLIC_DIRECTORY_PROFILES,
    USE_CLOUDINARY_STORAGE,
    USE_EMAIL_SERVICE,
    aliased,
    delete,
    exists,
    func,
    functools,
    json,
    literal,
    or_,
    os,
    redirect,
    request,
    select,
    update,
    url_for,
    logging,
)
from services.cloudinary_service import delete_media
from settings import Settings
from tasks import add_task_in_queue
from tasks.interface import follow
from utils import (
    AppError,
    BadRequestError,
    ConflictError,
    InternalServerError,
    ResourceNotFoundError,
    SuccessResponse,
    fname,
)

Log = logging.getLogger(__name__)


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

            # Notify the user that they are being followed
            add_task_in_queue(functools.partial(follow, user_id, session_user_id))
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

    redis_key = f"user:{_user_id or _username or _email}"
    cached_user = redis_client.get(redis_key)
    if cached_user:
        Log.info(f"Cache hit for user: {redis_key}")
        return SuccessResponse(
            data=json.loads(cached_user), message="Fetched user detail successfully"
        )

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
                select(1)
                .where(
                    Follower.follower_id == session_user_id,
                    Follower.user_id == Users.id,
                )
                .exists()
                .label(
                    "is_following"  # Whether session user follows or not
                ),
                Role.role,
            )
            .select_from(Users)
            .filter_by(**match_by)  # Apply matches to User only while in context
            .outerjoin(Role, Role.id == Users.role)
            .outerjoin(follower_count, follower_count.user_id == Users.id)
            .outerjoin(following_count, following_count.follower_id == Users.id)
            .outerjoin(Profile, Profile.user_id == Users.id)
            .group_by(Users.id, Profile.id, Role.id)
        )
        user = session.execute(stmt).first()

        if user:
            users_dict = {
                "user_id": user[0].id,
                "name": user[0].name,
                "username": user[0].username,
                "email": user[0].email if session_user_id == user[0].id else "",
                "join_date": user[0].created_at.isoformat(),
                "role": user.role,
                "account_status": user[0].account_status.value,
                "bio": user[1],
                "country": user[2],
                "profile_img_url": user[3]
                if USE_CLOUDINARY_STORAGE
                else f"{Settings.API_ROOT_URL or (request.host_url)[:-1]}{url_for('return_assets.serve_image', filename=fname(user[4], user[5]))}",
                "follower_count": user[6],
                "following_count": user[7],
                "is_following": user[8],
            }
            redis_client.set(redis_key, json.dumps(users_dict), ex=100)
            Log.info(f"Cache miss for user: {redis_key}")
            return SuccessResponse(
                data=users_dict, message="Fetched user detail successfully"
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
        redis_key = f"user:{user.username}"
        if name:
            # Update the name
            user.name = name
            session.commit()

        update_obj = {}
        if bio:
            update_obj["bio"] = bio
        if age:
            update_obj["age"] = age
        if country:
            update_obj["country"] = country

        if update_obj:
            stmt = (
                update(Profile)
                .where(Profile.user_id == session_user_id)
                .values(**update_obj)
            )
            session.execute(stmt)
            session.commit()
        redis_client.delete(redis_key)
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
                BlockedUsers.blocked_to == user_id,
                BlockedUsers.user_id == session_user_id,
            )
        )
        user = session.scalar(stmt)

        if not user:
            blocked_user = BlockedUsers(user_id=session_user_id, blocked_to=user_id)
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
                BlockedUsers.blocked_to == user_id,
                BlockedUsers.user_id == session_user_id,
            )
        )
        user = session.scalar(stmt)

        # Remove the user from the table
        if user:
            stmt = delete(BlockedUsers).where(
                BlockedUsers.blocked_to == user_id,
                BlockedUsers.user_id == session_user_id,
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


def _get_user_avatar(username: str):
    session = SessionLocal()
    try:
        user = (
            session.query(
                Users.username,
                Profile.media_url,
                Profile.media_public_id,
                Profile.file_extension,
                Profile.file_type,
            )
            .join(Profile, Profile.user_id == Users.id)
            .filter(Users.username == username)
            .first()
        )
        if not user:
            return redirect(url_for("return_assets.serve_image", filename="default"))

        return redirect(
            user[1]
            if USE_CLOUDINARY_STORAGE
            else f"{Settings.API_ROOT_URL or (request.host_url)[:-1]}{url_for('return_assets.serve_image', filename=fname(user[2], user[3]))}"
        )
    except AppError:
        raise
    except Exception as e:
        raise InternalServerError("Error while fetching user avatar") from e
    finally:
        session.close()


def _get_users_followers(
    user_id: int,
    session_user_id: int,
    limit: int = 15,
    offset: int = 0,
):
    join_model = Follower
    join_condition = Users.id == Follower.follower_id
    where_condition = [Follower.user_id == user_id]

    users = _fetch_users_follower_and_blocked_user(
        join_model=join_model,
        join_condition=join_condition,
        where_condition=where_condition,
        session_user_id=session_user_id,
        limit=limit,
        offset=offset,
    )
    return users


def _get_users_followings(
    user_id: int,
    session_user_id: int,
    limit: int = 15,
    offset: int = 0,
):
    join_model = Follower
    join_condition = Follower.user_id == Users.id
    where_condition = [Follower.follower_id == user_id]

    users = _fetch_users_follower_and_blocked_user(
        join_model=join_model,
        join_condition=join_condition,
        where_condition=where_condition,
        session_user_id=session_user_id,
        limit=limit,
        offset=offset,
    )
    return users


def _get_users_blocked_users(
    user_id: int,
    session_user_id: int,
    limit: int = 15,
    offset: int = 0,
):
    join_model = BlockedUsers
    join_condition = BlockedUsers.blocked_to == Users.id
    where_condition = [BlockedUsers.user_id == user_id]

    users = _fetch_users_follower_and_blocked_user(
        join_model=join_model,
        join_condition=join_condition,
        where_condition=where_condition,
        session_user_id=session_user_id,
        limit=limit,
        offset=offset,
    )
    return users


def _fetch_users_follower_and_blocked_user(
    join_model,
    join_condition,
    where_condition,
    session_user_id: int | None,
    limit: int = 15,
    offset: int = 0,
):
    session = SessionLocal()

    try:
        redis_key = f"post-detail:{request.path}:{request.remote_addr}"

        cached_data = redis_client.get(redis_key)
        if cached_data:
            fetched_users = json.loads(cached_data)
            Log.info("Redis hit post's interected users")
            return SuccessResponse(
                data=fetched_users, message="Fetched data", status_code=200
            )
        FollowerAlias = aliased(Follower)
        stmt = (
            (
                select(
                    Users.id,
                    Users.username,
                    Users.name,
                    Profile.media_url,
                    Profile.media_public_id,
                    Profile.file_extension,
                    Profile.file_type,
                    select(1)
                    .where(
                        FollowerAlias.user_id == Users.id,
                        FollowerAlias.follower_id == session_user_id,
                    )
                    .exists()
                    .label("is_following")
                    if session_user_id
                    else literal(False).label("is_following"),
                )
                .outerjoin_from(Users, Profile, Users.id == Profile.user_id)
                .join_from(Users, join_model, join_condition)
            )
            .where(*where_condition)
            .limit(limit)
            .offset(offset)
        )

        result = session.execute(stmt).all()

        Log.info("DB miss post's interected users")
        fetched_users = [
            {
                "user_id": user.id,
                "username": user.username,
                "name": user.name,
                "profile_img_url": user.media_url
                if USE_CLOUDINARY_STORAGE
                else f"{Settings.API_ROOT_URL or (request.host_url)[:-1]}{url_for('return_assets.serve_image', filename=fname(user.media_public_id, user.file_extension))}",
                "file_extension": user.file_extension,
                "file_type": user.file_type,
                "is_following": user.is_following,
            }
            for user in result
        ]
        redis_client.set(redis_key, json.dumps(fetched_users), ex=110)
        return SuccessResponse(
            data=fetched_users, message="Fetched data", status_code=200
        )

    finally:
        session.close()
