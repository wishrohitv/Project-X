from config import API_ENDPOINTS
from middlewares import verify_request_middleware
from modules import Blueprint, request
from repository.notification_repository import (
    _get_notifications,
    _track_notification_click,
    _unread_count_notification,
)
from utils import (
    BadRequestError,
    Log,
    LoggedUser,
    RateLimitExceededError,
    SuccessResponse,
)
from utils.logger import Logging

notification_blueprint = Blueprint("notifications", __name__)

route = API_ENDPOINTS()
logger = Logging(__name__)


# /notifications GET
@notification_blueprint.route(
    f"{route.notifications.route_name}", methods=route.notifications.methods
)
@verify_request_middleware(route.notifications)
def get_notifications(logged_user: LoggedUser, *args, **kwargs):

    session_user_id = logged_user.user_id
    mention = str(request.args.get("mention", default=False)).lower() == "true"
    limit = request.args.get("limit", default=15, type=int)
    offset = request.args.get("offset", default=0, type=int)

    return _get_notifications(session_user_id, mention, limit=limit, offset=offset)


# /notifications/unread-count GET
@notification_blueprint.route(
    f"{route.notifications_unread_count.route_name}",
    methods=route.notifications_unread_count.methods,
)
@verify_request_middleware(route.notifications_unread_count)
def unread_count_notifications(logged_user: LoggedUser, *args, **kwargs):

    session_user_id = logged_user.user_id
    return _unread_count_notification(session_user_id)


# /notifications/<int:notification_id>/clicked PATCH
@notification_blueprint.route(
    route.notifications_track.route_name, methods=route.notifications_track.methods
)
@verify_request_middleware(route.notifications_track)
def track_notification_click(logged_user: LoggedUser, *args, **kwargs):
    session_user_id = logged_user.user_id
    notification_id = kwargs["notification_id"]
    return _track_notification_click(session_user_id, notification_id)
