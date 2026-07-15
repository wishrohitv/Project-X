from database import SessionLocal, redis_client
from models import Posts, Users
from modules import APP_NAME

# from repository.post_repository import _create_post
from services.bot_service import gemini_agent, generate_bot_response
from utils import Logging, get_usernames

log = Logging(__name__)


def process_user_requests(
    parent_post_id: int | None,
    current_post_id: int,
    replying_to: list[str] | None,  # List of username of the user who are in the thread
    text: str = "",
):
    session = SessionLocal()

    if "nara" not in get_usernames(text):
        return

    # Set rate limit
    # TODO: Implement rate limiting
    key = f"rate_limit_agent:{current_post_id}"
    if redis_client.exists(key):
        log.info(f"Rate limit exceeded for agent: {key}")
        return
    redis_client.set(key, 1, ex=60)  # 1 request per minute

    try:
        current_post = (
            session.query(Posts, Users.username)
            .join(Users, Posts.user_id == Users.id)
            .filter(
                Posts.id == current_post_id,
                Posts.visibility,
            )
            .first()
        )

        if not current_post:
            return

        result = gemini_agent(
            current_post[0].user_id, current_post[0].text, parent_post_id
        )

        log.info(f"Agent call completed: result={result[:10] if result else None}")

        if not result:
            return

        # Create post for this response
        from repository.post_repository import _create_post

        if replying_to is None:
            replying_to = [current_post[1]]
        else:
            replying_to = sorted(set(replying_to + [current_post[1]]))

        _create_post(
            user_id=32,  # Default user_id for bot, representing the bot itself
            text=result,
            tags=None,
            media_url=None,
            media_public_id=None,
            file_type=None,
            file_extension=None,
            age_rating="pg13",
            category=1,
            parent_post_id=current_post_id,
            is_reply=True,
            visibility=True,
            replying_to=replying_to,
        )

    except Exception as e:
        raise e
