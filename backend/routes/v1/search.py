from config import API_ENDPOINTS
from middlewares import verify_request_middleware
from modules import Blueprint, request
from repository.search_repository import (
    _posts_by_hashtag,
    _search_by_posts,
    _search_by_users,
    _search_prediction,
    _trending_hashtags,
)
from sqlalchemy.sql.functions import session_user
from utils import BadRequestError, LoggedUser, SuccessResponse

search_blueprint = Blueprint("search", __name__)

route = API_ENDPOINTS()


# /search GET
@search_blueprint.route(route.search.route_name, methods=route.search.methods)
@verify_request_middleware(route.search)
def search(logged_user: LoggedUser | None):
    session_user_id = logged_user.user_id if logged_user else None
    query = request.args.get("q")
    limit = request.args.get("limit", default=10, type=int)
    offset = request.args.get("offset", default=0, type=int)
    filter_by = request.args.get("filter_by", default="all")
    if not query or query.strip() == "":
        raise BadRequestError("No search query found")
    if filter_by not in ["people", "post", "all"]:
        raise BadRequestError("Invalid filter flag")
    if limit > 10 or offset > 10:
        raise BadRequestError(
            "Invalid limit or offset, limit can't be greater than 10 and offset 10"
        )
    if filter_by == "people":
        return _search_by_users(query, session_user_id, limit, offset)
    if filter_by == "post":
        return _search_by_posts(query, limit, offset)
    return _search_prediction(query)


# /search/suggestion GET
@search_blueprint.route(
    route.search_suggestion.route_name, methods=route.search_suggestion.methods
)
def search_predict():
    query = request.args.get("q")
    if not query or query.strip() == "":
        raise BadRequestError("No search query found")
    return _search_prediction(query)


# /trending GET
@search_blueprint.route(route.trending.route_name, methods=route.trending.methods)
def trending():
    # TODO: Fetch trending hashtags(text prefix with #) by filtering post text
    """
    Trending hashtags
    Fetch trending hashtags by filtering post text
    """
    return _trending_hashtags()


# /trending/<string:hash_tag>/post GET
@search_blueprint.route(
    route.trending_posts.route_name, methods=route.trending_posts.methods
)
def trending_posts(hash_tag: str):
    """
    Trending posts
    Fetch post by filtering post text
    """
    limit = request.args.get("limit", default=10)
    offset = request.args.get("offset", default=0)

    if int(limit) > 10 or int(offset) > 10:
        raise BadRequestError("Invalid limit or offset")

    return _posts_by_hashtag(hash_tag, int(limit), int(offset))
