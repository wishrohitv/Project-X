from database import redis_client
from models import Posts
from modules import APP_NAME
from services.bot_service import generate_bot_response


def process_user_requests(
    parentPostID: int | None,
    currentPostID: int,
    userName: str,
    text: str,
):
    # Set rate limit
    # TODO: Implement rate limiting
    if parentPostID:
        parentPost = _getPostByIDorPostRepliesByID(postID=parentPostID)

        currentPost = _getPostByIDorPostRepliesByID(postID=currentPostID)

    query = {
        "role": f"Chat bot of {APP_NAME}(similar to x/twitter) and your name is nara, context can be empty, don't mention about yourself unless you are explicitily asked,  don't mention usernames unless it is required",
        "context": "user:@anme post:'This is the best movie i have ever seen, avenger is a best movie'",
        "task": "user:@john post:'Hi @nara can you explain about the post'",
    }
    response = generate_bot_response(text)
