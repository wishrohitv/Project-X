from database import SessionLocal, redis_client
from models import Notifications
from models.enums import NotificationType
from modules import func, json, or_, select
from utils import (
    AppError,
    BadRequestError,
    ConflictError,
    InternalServerError,
    Logging,
    ResourceNotFoundError,
    SuccessResponse,
    datetime_utc,
)

Log = Logging(__name__)


def _create_notification(
    user_id: int | None,
    notice: dict,
    type: NotificationType,
):
    session = SessionLocal()
    try:
        notification = Notifications(
            user_id=user_id,
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
            session.query(Notifications)
            .filter(*condition)
            .offset(offset)
            .limit(limit)
            .all()
        )

        if not result:
            raise ResourceNotFoundError("No notification found")
        notifications = [
            {
                "id": notice.id,
                "type": notice.type.value,
                "notice": notice.notice,
                "created_at": notice.created_at.isoformat(),
                "updated_at": notice.updated_at.isoformat(),
                "read_at": notice.read_at.isoformat()
                if notice.read_at is not None
                else notice.read_at,
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
