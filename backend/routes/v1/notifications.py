from config import API_ENDPOINTS
from middlewares.verify_client_request import verify_request_middleware
from modules import Blueprint, make_response, request
from repository.notificationRepository import _getNotifications
from utils import Log, LoggedUser
from utils.app_errors import RateLimitExceededError
from utils.logger import Logging

notificationBlueprint = Blueprint("notifications", __name__)

route = API_ENDPOINTS()
logger = Logging(__name__)


@notificationBlueprint.route(
    f"{route.get_notifications.route_name}", methods=route.get_notifications.methods
)
@verify_request_middleware(route.get_notifications.route_name)
def get_notifications(logged_user: LoggedUser, *args, **kwargs):
    try:
        sessionUserID = logged_user.user_id
        mention = str(request.args.get("mention", default=False)).lower() == "true"
        notice = _getNotifications(sessionUserID, mention)
        return notice
    except Exception as e:
        Log.error(e)
        return make_response({"error": str(e)}, 500)


@notificationBlueprint.route(
    route.track_notifications.route_name, methods=route.track_notifications.methods
)
@verify_request_middleware(route.track_notifications.route_name)
def track_notification_click():
    # TODO: complete the logic
    logger.error("not fuond")
    raise RateLimitExceededError("Bad request")
