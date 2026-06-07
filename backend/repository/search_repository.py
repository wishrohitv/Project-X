from database import SessionLocal
from models import Posts, Profile, Users
from modules import (
    API_ROOT_URL,
    USE_CLOUDINARY_STORAGE,
    and_,
    or_,
    request,
    select,
    url_for,
)
from utils import BadRequestError, InternalServerError, SuccessResponse

from .feed_repository import _query_posts


def _search_by_users(text: str, limit: int = 10, offset: int = 0):
    session = SessionLocal()
    value = f"%{text}%"
    try:
        stmt = (
            select(
                Users.username,
                Users.name,
                Profile.media_url,
                Profile.media_public_id,
                Profile.file_extension,
            )
            .join(Profile, Users.id == Profile.user_id)
            .where(or_(Users.username.ilike(value), Users.name.ilike(value)))
            .limit(limit)
            .offset(offset)
        )
        result = session.execute(stmt).all()
        matched_users = [
            {
                "username": user[0],
                "name": user[1],
                "profile_img_url": [2]
                if USE_CLOUDINARY_STORAGE
                else f"{API_ROOT_URL or request.host_url}{url_for('return_assets.serve_image', filename=f'{user[3]}.{user[4]}')}",
            }
            for user in result
        ]

        return SuccessResponse(data=matched_users)
    except Exception as e:
        raise InternalServerError("Error while searching by users") from e
    finally:
        session.close()


def _search_by_posts(text: str, limit: int = 10, offset: int = 0):
    session = SessionLocal()
    value = f"%{text}%"
    try:
        conditions = [or_(Posts.text.ilike(value), Posts.tags.ilike(value))]
        posts = _query_posts(
            conditions=conditions,
            category=[],
            offset=offset,
            limit=limit,
        )

        return SuccessResponse(data=posts, message="Posts fetched successfully")
    except Exception as e:
        raise InternalServerError("Error while searching by posts") from e
    finally:
        session.close()


def _search_prediction(text: str):
    # Text can username or name
    value = f"%{text}%"
    session = SessionLocal()
    try:
        stmt = (
            select(
                Users.username,
                Users.name,
                Profile.media_url,
                Profile.media_public_id,
                Profile.file_extension,
            )
            .outerjoin(Profile, Users.id == Profile.user_id)
            .where(or_(Users.username.ilike(value), Users.name.ilike(value)))
            .limit(20)
        )
        result = session.execute(stmt).all()
        matched_users = [
            {
                "username": user[0],
                "name": user[1],
                "profile_img_url": [2]
                if USE_CLOUDINARY_STORAGE
                else f"{API_ROOT_URL or request.host_url}{url_for('return_assets.serve_image', filename=f'{user[3]}.{user[4]}')}",
            }
            for user in result
        ]

        return SuccessResponse(
            data=matched_users, message="Fetch data successfully", status_code=200
        )
    except Exception as e:
        raise InternalServerError("Error while predicting search") from e
    finally:
        session.close()
