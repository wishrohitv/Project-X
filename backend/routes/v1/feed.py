from config import API_ENDPOINTS
from middlewares import rate_limiter_middleware, verify_request_middleware
from modules import Blueprint, request
from repository.feed_repository import _get_home_feed, _get_home_feed_followings
from utils import BadRequestError, LoggedUser, SuccessResponse

feed_blueprint = Blueprint("feed", __name__)

route = API_ENDPOINTS()


# /feed GET
@feed_blueprint.route(route.feed.route_name, methods=route.feed.methods)
@rate_limiter_middleware(route.feed)
@verify_request_middleware(route.feed)
def get_feed(logged_user: LoggedUser | None = None, *args, **kwargs):
    """
    Check if user is logged then build home feed based on his interests
    """
    offset = request.args.get("offset", type=int, default=0)
    limit = request.args.get("limit", type=int, default=10)
    category_ids = request.args.get("category", type=list, default=[1])
    template = str(request.args.get("template", default="False")).lower() == "true"
    session_user_id: int | None = logged_user.user_id if logged_user else None

    if limit == 0 or limit > 30:
        raise BadRequestError("Invalid limit")

    return _get_home_feed(
        category=category_ids,
        offset=offset,
        limit=limit,
        session_user_id=session_user_id,
        fetch_template=template,
    )


# /feed/followings GET
@feed_blueprint.route(
    route.feed_followings.route_name, methods=route.feed_followings.methods
)
@rate_limiter_middleware(route.feed_followings)
@verify_request_middleware(route.feed_followings)
def get_feed_followings(logged_user: LoggedUser, *args, **kwargs):
    """
    Check if user is logged then build home feed based on his interests
    """
    offset = request.args.get("offset", type=int, default=0)
    limit = request.args.get("limit", type=int, default=10)
    session_user_id: int = logged_user.user_id

    if limit == 0 or limit > 30:
        raise BadRequestError("Invalid limit")

    return _get_home_feed_followings(
        session_user_id=session_user_id,
        offset=offset,
        limit=limit,
    )
