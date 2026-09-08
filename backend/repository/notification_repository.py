from database import SessionLocal, redis_client
from models import Notifications, Profile, Users
from models.enums import NotificationType
from modules import (
    USE_CLOUDINARY_STORAGE,
    func,
    json,
    logging,
    or_,
    request,
    select,
    url_for,
)
from settings import Settings
from utils import (
    AppError,
    BadRequestError,
    ConflictError,
    InternalServerError,
    ResourceNotFoundError,
    SuccessResponse,
    datetime_utc,
    fname,
)

Log = logging.getLogger(__name__)


def _create_notification(
    user_id: int | None,
    author_user_id: int | None,
    notice: dict[str, str | int] | None,
    type: NotificationType,
):
    session = SessionLocal()
    try:
        notification = Notifications(
            user_id=user_id,
            author_user_id=author_user_id,
            notice=notice,
            type=type,
        )
        session.add(notification)
        session.commit()

    except Exception as e:
        session.rollback()
        raise InternalServerError(str(e))
    finally:
        session.close()


def _get_notifications(
    session_user_id: int, mention: bool = False, limit: int = 15, offset: int = 0
):
    session = SessionLocal()

    redis_key = f"notifications:{session_user_id}:{offset}:{limit}:mention:{mention}"

    cached_result = redis_client.get(redis_key)
    if cached_result:
        Log.info("Redis cache hit for notifications")
        return SuccessResponse(
            data=json.loads(cached_result),
            message="Notification fetched successfully",
            status_code=200,
        )

    condition = []
    if mention:
        condition.append(Notifications.type == NotificationType.mention)
        condition.append(
            Notifications.user_id == session_user_id,
        )
    else:
        condition.append(
            or_(
                Notifications.user_id == session_user_id,
                Notifications.user_id.is_(None),
            )
        )

    try:
        result = (
            session.query(
                Notifications,
                Users.username,
                Profile.media_url,
                Profile.media_public_id,
                Profile.file_extension,
                Profile.file_type,
            )
            .outerjoin(Users, Users.id == Notifications.author_user_id)
            .outerjoin(Profile, Users.id == Profile.user_id)
            .filter(*condition)
            .order_by(Notifications.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

        if not result:
            raise ResourceNotFoundError("No notification found")

        notifications = [
            {
                "id": notice[0].id,
                "type": notice[0].type.value,
                "notice": notice[0].notice,
                "created_at": notice[0].created_at.isoformat(),
                "updated_at": notice[0].updated_at.isoformat(),
                "read_at": notice[0].read_at.isoformat()
                if notice[0].read_at is not None
                else notice[0].read_at,
                "user": {
                    "user_id": notice[0].author_user_id,
                    "username": notice.username,
                    "profile_img_url": notice.media_url
                    if USE_CLOUDINARY_STORAGE
                    else f"{Settings.API_ROOT_URL or (request.host_url)[:-1]}{url_for('return_assets.serve_image', filename=fname(notice.media_public_id, notice.file_extension))}",
                }
                if notice[0].author_user_id
                else None,
            }
            for notice in result
        ]
        Log.info("Redis cache miss for notifications")
        redis_client.set(redis_key, json.dumps(notifications), ex=120)
        return SuccessResponse(
            data=notifications,
            message="Notification fetched successfully",
            status_code=200,
        )
    except AppError:
        raise
    except Exception as e:
        raise InternalServerError("Error while fetching notifications") from e
    finally:
        session.close()


def _track_notification_click(session_user_id: int, notification_id: int):
    session = SessionLocal()
    try:
        notification = (
            session.query(Notifications)
            .filter_by(user_id=session_user_id, id=notification_id)
            .first()
        )
        if not notification:
            raise BadRequestError("Invalid notification id")

        if notification.read_at:
            raise ConflictError("Notificatoin is already read")

        # Update the notification
        notification.read_at = datetime_utc()
        session.commit()

        return SuccessResponse(data={})
    except AppError:
        raise
    except Exception as e:
        session.rollback()
        raise InternalServerError("Error while fetching notifications") from e
    finally:
        session.close()


def _unread_count_notification(session_user_id: int):
    session = SessionLocal()
    try:
        stmt = select(func.count(Notifications.id)).filter_by(
            user_id=session_user_id, read_at=None
        )
        result = session.execute(stmt).scalar()
        return SuccessResponse(data={"count": result or 0})
    except AppError:
        raise
    except Exception as e:
        raise InternalServerError("Error while fetching notifications") from e
    finally:
        session.close()
