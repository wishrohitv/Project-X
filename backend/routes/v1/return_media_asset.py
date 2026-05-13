from constant import USE_CLOUDINARY_STORAGE
from modules import (
    PUBLIC_DIRECTORY_POSTS,
    PUBLIC_DIRECTORY_PROFILES,
    USE_CLOUDINARY_STORAGE,
    Blueprint,
    Response,
    make_response,
    os,
    requests,
    send_file,
    send_from_directory,
    url_for,
)
from repository.post_repository import _get_post_media
from utils import Log

return_media_assets_blueprint = Blueprint("return_assets", __name__)


@return_media_assets_blueprint.route("/getPostMedia/<int:postID>")
def getPostMedia(postID):
    """
    Get the media file associated with a post.
    NOTE: If multifile support is added in post in future, make sure to handle it accordingly.
    Args:
        postID (int): The ID of the post.

    Returns:
        Response: The media file as an attachment.
    """
    post: tuple[str, str, str, str] | None = _getPostMedia(postID)
    if not post:
        return Response("File not found", status=404)
    if USE_CLOUDINARY_STORAGE:
        file = requests.get(post[1], stream=True)
        return Response(
            file.iter_content(chunk_size=8192),
            headers={
                "Content-Disposition": f'attachment; filename="{post[0]}.{post[3]}"',
                "Content-Type": file.headers.get(
                    "Content-Type", "application/octet-stream"
                ),
            },
        )
    else:
        fileName = f"{post[2]}.{post[3]}"
        if os.path.exists(os.path.join(PUBLIC_DIRECTORY_POSTS, fileName)):
            return send_file(
                f"{PUBLIC_DIRECTORY_POSTS.replace('./backend/', '')}/{fileName}",
                as_attachment=True,
                download_name=f"{post[0]}.{post[3]}",
            )
        else:
            return Response("File not found", status=404)


@return_media_assets_blueprint.route("/postMedia/<path:fileName>")
def servePostMedia(fileName):
    if os.path.exists(os.path.join(PUBLIC_DIRECTORY_POSTS, fileName)):
        # return send_from_directory(PUBLIC_DIRECTORY_POSTS, fileName)

        return send_file(
            f"{PUBLIC_DIRECTORY_POSTS.replace('./backend/', '')}/{fileName}"
        )
    else:
        return send_from_directory(PUBLIC_DIRECTORY_POSTS, "icon")


@return_media_assets_blueprint.route(
    "/getProfileImage/<string:userName>", methods=["GET"]
)
def getProfileImage(userName):
    return make_response(
        {
            "profileImg": url_for(
                "profileImage.serveImage", fileName=userName, _external=True
            )
        },
        200,
    )


@return_media_assets_blueprint.route("/userProfile/<path:fileName>")
def serveImage(fileName):
    if os.path.exists(os.path.join(PUBLIC_DIRECTORY_PROFILES, fileName)):
        Log.info(f"userProfile {fileName} found")
        return send_file(
            f"{PUBLIC_DIRECTORY_PROFILES.replace('/backend', '')}/{fileName}"
        )
    else:
        Log.warning(f"userProfile {fileName} not found, Sending default image")
        return send_from_directory(
            PUBLIC_DIRECTORY_PROFILES.replace("/backend", ""), "icon"
        )
