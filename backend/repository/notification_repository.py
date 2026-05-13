from database import engine
from models import Notifications
from models.enums import NotificationType
from modules import make_response, or_, sessionmaker
from utils import Log

Session = sessionmaker(bind=engine)
session = Session()


def _create_notification(
    user_id: int | None,
    notice: dict,
    type: NotificationType,
):
    try:
        notification = Notifications(
            user_id=user_id,
            notice=notice,
            type=type,
        )
        session.add(notification)
        session.commit()
        session.close()
    except Exception as e:
        session.rollback()
        session.close()
        Log.critical(f"Error creating notification: {str(e)}")
        raise Exception(str(e))


def _get_notifications(session_user_id: int, mention: bool = False, offset: int = 0):
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
            .limit(10)
            .all()
        )

        if not result:
            return make_response([], 200)
        notifications = [
            {
                "id": notice.id,
                "type": notice.type.value,
                "notice": notice.notice,
                "created_at": notice.created_at,
                "updated_at": notice.updated_at,
                "read_at": notice.read_at,
            }
            for notice in result
        ]
        return make_response(notifications, 200)
    except Exception as e:
        Log.error(e)
        return make_response({"error": "Internal sever error"}, 500)
