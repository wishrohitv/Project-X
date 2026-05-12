from database import engine
from flask.helpers import make_response
from models import Notifications
from models.enums import NotificationType
from modules import or_, sessionmaker
from utils import Log

Session = sessionmaker(bind=engine)
session = Session()


def _createNotification(
    userID: int | None,
    notice: dict,
    type: NotificationType,
):
    try:
        notification = Notifications(
            userID=userID,
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


def _getNotifications(sessionUserID: int, mention: bool = False, offset: int = 0):
    condition = []
    if mention:
        condition.append(Notifications.type == NotificationType.mention)
        condition.append(
            Notifications.userID == sessionUserID,
        )
    else:
        condition.append(
            or_(
                Notifications.userID == sessionUserID,
                Notifications.userID.is_(None),
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
                "createdAt": notice.createdAt,
                "updatedAt": notice.updatedAt,
                "readAt": notice.readAt,
            }
            for notice in result
        ]
        return make_response(notifications, 200)
    except Exception as e:
        Log.error(e)
        return make_response({"error": "Internal sever error"}, 500)
