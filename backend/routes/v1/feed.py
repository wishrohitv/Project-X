from config import API_ENDPOINTS
from middlewares.verify_client_request import verify_request_middleware
from modules import Blueprint, make_response, request
from repository.feed_repository import getHomeFeed
from utils import LoggedUser

feed_blueprint = Blueprint("feed", __name__)

route = API_ENDPOINTS()


# /feed
@feed_blueprint.route(route.feed.route_name, methods=route.feed.methods)
@verify_request_middleware(route.feed.route_name)
def getFeed(logged_user: LoggedUser | None = None, *args, **kwargs):
    """
    Check if user is logged then build home feed based on his interests
    """
    offset = request.args.get("offset", type=int, default=0)
    limit = request.args.get("limit", type=int, default=10)
    category_ids = request.args.get("category", type=list, default=[1])
    template = str(request.args.get("template", default="False")).lower() == "true"
    session_user_ids: int | None = logged_user.user_id if logged_user else None
    print(request.args.get("template", default="False"))
    if limit == 0 or limit > 30:
        return make_response({"error": "Invalid limit"}, 400)
    try:
        return getHomeFeed(
            category=category_ids,
            offset=offset,
            limit=limit,
            session_user_ids=session_user_ids,
            fetchTemplate=template,
        )
    except Exception as e:
        return make_response({"error": str(e)}, 500)
