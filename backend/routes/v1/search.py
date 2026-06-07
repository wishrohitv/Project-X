from config import API_ENDPOINTS
from modules import Blueprint, request
from repository.search_repository import _search_prediction
from utils import BadRequestError, SuccessResponse

search_blueprint = Blueprint("search", __name__)

route = API_ENDPOINTS()


@search_blueprint.route(route.search.route_name, methods=route.search.methods)
def search():
    query = request.args.get("q")
    limit = request.args.get("limit", default=10)
    offset = request.args.get("offset", default=0)
    filter_by = request.args.get("filter_by", default="all")

    if filter_by not in ["people", "post", "all"]:
        raise BadRequestError("Invalid filter flag")
    if int(limit) > 15 or int(offset) > 10:
        raise BadRequestError("Invalid limit or offset")

    return SuccessResponse(data={}, message="Fetch data successfully", status_code=200)


@search_blueprint.route(
    route.search_suggestion.route_name, methods=route.search_suggestion.methods
)
def search_predict():
    query = request.args.get("q")
    if not query or query.strip() == "":
        raise BadRequestError("No search query found")
    return _search_prediction(query)


@search_blueprint.route(route.trending.route_name, methods=route.trending.methods)
def trending():
    """
    Trending hashtags
    Fetch trending hashtags by filtering post text
    """
    return SuccessResponse(data={}, message="Fetch data successfully", status_code=200)


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

    if int(limit) > 15 or int(offset) > 10:
        raise BadRequestError("Invalid limit or offset")

    return SuccessResponse(data={}, message="Fetch data successfully", status_code=200)
