from config import API_ENDPOINTS
from middlewares.verify_client_request import verify_request_middleware
from modules import Blueprint, make_response, request
from repository.collection_repository import (
    _addPostToCollection,
    _createCollection,
    _deleteCollection,
    _removePostToCollection,
)
from utils import LoggedUser

collection_blueprint = Blueprint("collections", __name__)


route = API_ENDPOINTS()


@collection_blueprint.route(
    route.collection.routeName, methods=route.collection.methods
)
@verify_request_middleware(route.collection.routeName)
def collection(loggedUser: LoggedUser, *args, **kwargs):
    return make_response({}, 201)


# /collections/create
@collection_blueprint.route(
    route.createCollection.routeName, methods=route.createCollection.methods
)
@verify_request_middleware(route.createCollection.routeName)
def createCollection(loggedUser: LoggedUser, *args, **kwargs):
    sessionUserID = loggedUser.userID
    body = request.get_json()
    collectionName = body.get("collectionName")
    description = body.get("description")
    if not collectionName:
        return make_response({"error": "Collection name is required"}, 400)
    try:
        _createCollection(collectionName, sessionUserID, description)
        return make_response({"message": "Collection created successfully"}, 201)
    except Exception as e:
        return make_response({"error": str(e)}, 500)


# /collections/addPost
@collection_blueprint.route(
    f"{route.addPostToCollection.routeName}/<int:collectionID>/<int:postID>",
    methods=route.addPostToCollection.methods,
)
@verify_request_middleware(route.addPostToCollection.routeName)
def addPost(loggedUser: LoggedUser, *args, **kwargs):
    sessionUserID = loggedUser.userID
    collectionID = kwargs.get("collectionID")
    postID = kwargs.get("postID")
    if not collectionID or not postID:
        return make_response({"error": "Collection ID and Post ID are required"}, 400)
    try:
        _addPostToCollection(collectionID, sessionUserID, postID)
        return make_response({"message": "Post added to collection successfully"}, 201)
    except Exception as e:
        return make_response({"error": str(e)}, 500)


# /collections/removePost
@collection_blueprint.route(
    f"{route.removePostFromCollection.routeName}/<int:collectionID>/<int:postID>",
    methods=route.removePostFromCollection.methods,
)
@verify_request_middleware(route.removePostFromCollection.routeName)
def removePosts(loggedUser: LoggedUser, *args, **kwargs):
    sessionUserID = loggedUser.userID
    collectionID = kwargs.get("collectionID")
    postID = kwargs.get("postID")
    if not collectionID or not postID:
        return make_response({"error": "Collection ID and Post ID are required"}, 400)
    try:
        _removePostToCollection(collectionID, sessionUserID, postID)
        return make_response(
            {"message": "Post removed from collection successfully"}, 200
        )
    except Exception as e:
        return make_response({"error": str(e)}, 500)


# /collections/deleteCollection
@collection_blueprint.route(
    f"{route.deleteCollection.routeName}/<int:collectionID>",
    methods=route.deleteCollection.methods,
)
@verify_request_middleware(route.deleteCollection.routeName)
def deleteCollection(loggedUser: LoggedUser, *args, **kwargs):
    sessionUserID = loggedUser.userID
    collectionID = kwargs.get("collectionID")
    if not collectionID:
        return make_response({"error": "Collection ID is required"}, 400)
    try:
        _deleteCollection(collectionID, sessionUserID)
        return make_response({"message": "Collection deleted successfully"}, 200)
    except Exception as e:
        return make_response({"error": str(e)}, 500)
