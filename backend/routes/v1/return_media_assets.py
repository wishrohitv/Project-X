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


@return_media_assets_blueprint.route("/get_post_media/<int:post_id>")
def get_post_media(post_id):
    """
    Get the media file associated with a post.
    NOTE: If multifile support is added in post in future, make sure to handle it accordingly.
    Args:
        post_id (int): The ID of the post.

    Returns:
        Response: The media file as an attachment.
    """
    post: tuple[str, str, str, str] | None = _get_post_media(post_id)
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
        filename = f"{post[2]}.{post[3]}"
        if os.path.exists(os.path.join(PUBLIC_DIRECTORY_POSTS, filename)):
            return send_file(
                f"{PUBLIC_DIRECTORY_POSTS.replace('./backend/', '')}/{filename}",
                as_attachment=True,
                download_name=f"{post[0]}.{post[3]}",
            )
        else:
            return Response("File not found", status=404)


@return_media_assets_blueprint.route("/post_media/<path:filename>")
def serve_post_media(filename):
    if os.path.exists(os.path.join(PUBLIC_DIRECTORY_POSTS, filename)):
        # return send_from_directory(PUBLIC_DIRECTORY_POSTS, filename)

        return send_file(
            f"{PUBLIC_DIRECTORY_POSTS.replace('./backend/', '')}/{filename}"
        )
    else:
        return send_from_directory(PUBLIC_DIRECTORY_POSTS, "icon")


@return_media_assets_blueprint.route(
    "/get_profile_image/<string:username>", methods=["GET"]
)
def get_profile_image(username):
    return make_response(
        {
            "profile_img": url_for(
                "profile_image.serve_image", filename=username, _external=True
            )
        },
        200,
    )


@return_media_assets_blueprint.route("/user_profile/<path:filename>")
def serve_image(filename):
    if os.path.exists(os.path.join(PUBLIC_DIRECTORY_PROFILES, filename)):
        Log.info(f"user_profile {filename} found")
        return send_file(
            f"{PUBLIC_DIRECTORY_PROFILES.replace('/backend', '')}/{filename}"
        )
    else:
        Log.warning(f"userProfile {filename} not found, Sending default image")
        return send_from_directory(PUBLIC_DIRECTORY_PROFILES, "icon")
