from config import API_ENDPOINTS
from middlewares import verify_request_middleware
from modules import Blueprint, make_response, request
from repository.collection_repository import (
    _add_post_to_collection,
    _create_collection,
    _delete_collection,
    _remove_post_to_collection,
)
from utils import BadRequestError, LoggedUser, SuccessResponse

collection_blueprint = Blueprint("collections", __name__)


route = API_ENDPOINTS()


@collection_blueprint.route(
    route.collection.route_name, methods=route.collection.methods
)
@verify_request_middleware(route.collection)
def collection(logged_user: LoggedUser, *args, **kwargs):
    return make_response({}, 201)


# /collections POST
@collection_blueprint.route(
    route.collection_create.route_name, methods=route.collection_create.methods
)
@verify_request_middleware(route.collection_create)
def create_collection(logged_user: LoggedUser, *args, **kwargs):
    session_user_id = logged_user.user_id
    body = request.get_json()
    name = body.get("name")
    description = body.get("description")
    if not name:
        raise BadRequestError("Collection name is required")

    _create_collection(name, session_user_id, description)
    return make_response({"message": "Collection created successfully"}, 201)


# /collections/<int:collection_id>/<int:post_id> POST
@collection_blueprint.route(
    route.collection_add_post.route_name,
    methods=route.collection_add_post.methods,
)
@verify_request_middleware(route.collection_add_post)
def add_post(logged_user: LoggedUser, *args, **kwargs):
    session_user_id = logged_user.user_id
    collection_id = kwargs["collection_id"]
    post_id = kwargs["post_id"]

    _add_post_to_collection(collection_id, session_user_id, post_id)
    return SuccessResponse(
        data={}, message="Post added to collection successfully", status_code=201
    )


# /collections/<int:collection_id>/<int:post_id> DELETE
@collection_blueprint.route(
    f"{route.collection_remove_post.route_name}",
    methods=route.collection_remove_post.methods,
)
@verify_request_middleware(route.collection_remove_post)
def remove_posts(logged_user: LoggedUser, *args, **kwargs):
    session_user_id = logged_user.user_id
    collection_id = kwargs["collection_id"]
    post_id = kwargs["post_id"]

    _remove_post_to_collection(collection_id, session_user_id, post_id)
    return SuccessResponse(
        data={},
        message="Post removed from collection successfully",
        status_code=200,
    )


# /collections/<int:collection_id> DELETE
@collection_blueprint.route(
    route.collection_delete.route_name,
    methods=route.collection_delete.methods,
)
@verify_request_middleware(route.collection_delete)
def delete_collection(logged_user: LoggedUser, *args, **kwargs):
    session_user_id = logged_user.user_id
    collection_id = kwargs["collection_id"]

    _delete_collection(collection_id, session_user_id)
    return SuccessResponse(
        data={},
        message="Collection deleted successfully",
        status_code=200,
    )
