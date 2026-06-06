from database import SessionLocal
from models import Posts, Users
from models.enums import NotificationType
from modules import sessionmaker
from repository.notification_repository import _create_notification
from utils import Log, get_usernames


def mention(
    mentioned_by_user_id: int,
    post_id: int,
    text: str,
) -> None | Exception:
    session = SessionLocal()
    try:
        # Extract mentioned usernames from the text
        mentioned_usernames = get_usernames(text)

        # Get the username of the user who mentioned others
        result = (
            session.query(Users.username)
            .filter(Users.id == mentioned_by_user_id)
            .first()
        )
        # Get the username of the user who mentioned others
        mentioned_by = result[0] if result else None

        # If the user who mentioned others is not found, we can't create notifications
        if not mentioned_by:
            return

        # Create notifications for each mentioned user
        for mentioned_username in mentioned_usernames:
            # Find the user ID of the mentioned username
            result = (
                session.query(Users.id)
                .filter(Users.username == mentioned_username)
                .first()
            )
            # User iD of the mentioned user, if found, else None
            user_id = result[0] if result else None

            # If the mentioned user is found, create a notification for them
            if user_id:
                notice = {
                    # Post ID where the user was mentioned
                    "post_id": post_id,
                    # Username of the user who mentioned them
                    "mentioned_by": mentioned_by,
                    # Text of the notification, e.g., "Alice mentioned you in a post."
                    "alert": f"{mentioned_by} mentioned you in a post.",
                    "text": text[150]
                    if len(text) > 150
                    else text,  # Short preview of the text
                }
                # Create the notification using the createNotification function
                _create_notification(
                    user_id=user_id,
                    notice=notice,
                    type=NotificationType.mention,
                )
    except Exception as e:
        session.close()
        raise Exception(str(e))
    finally:
        session.close()


def suggestion(
    post_id: int,
    user_id: list[int],  # list of user IDs to whom the suggestion is made
    text: str,  # title of the post or ""
) -> None | Exception:
    notice = {
        "post_id": post_id,
        "text": text[150] if len(text) > 150 else text,  # Short preview of the text,
    }

    for _user_id in user_id:
        # Create the notification using the createNotification function
        _create_notification(
            user_id=_user_id,
            notice=notice,
            type=NotificationType.suggestion,
        )


def reply(
    parent_post_id: int,
    post_id: int,
    mentioned_usernames_by_system: list[
        str
    ],  # list of usernames mentioned by system in the reply in the thread
    mentioned_by_user_id: int,  # user ID of post/reply author who mentioned others in the thread
    text: str,  # title of the post or ""
) -> None | Exception:
    session = SessionLocal()
    try:

        def create_mention_notification(
            mentioned_username: str,
            _user_id: int,
            _notice: dict,
            type: NotificationType,
        ):
            # Find the user ID of the mentioned username
            result = (
                session.query(Users.id)
                .filter(Users.username == mentioned_username)
                .first()
            )
            # User iD of the mentioned user, if found, else None
            user_id = result[0] if result else None

            # If the mentioned user is found, create a notification for them
            if user_id:
                # Create the notification using the createNotification function
                _create_notification(
                    user_id=user_id,
                    notice=_notice,
                    type=type,
                )

        # Extract mentioned usernames from the text
        mentioned_usernames = get_usernames(text)

        # Get the username of the user who mentioned others
        result = (
            session.query(Users.username)
            .filter(Users.id == mentioned_by_user_id)
            .first()
        )
        # Get the username of the user who mentioned others
        mentioned_by = result[0] if result else None

        # If the user who mentioned others is not found, we can't create notifications
        if not mentioned_by:
            return

        # Create notifications for each mentioned user by the system (e.g., if the system automatically mentions users in a thread)
        for mentioned_username in mentioned_usernames_by_system:
            if mentioned_by == mentioned_username:
                continue  # Skip if the user mentioned themselves

            notice = {
                # Post ID where the user was mentioned
                "post_id": post_id,
                # Username of the user who mentioned them
                "mentioned_by": mentioned_by,
                # Text of the notification, e.g., "Alice mentioned you in a post."
                "alert": f"{mentioned_by} is replied you.",
                "text": text[150]
                if len(text) > 150
                else text,  # Short preview of the text
            }
            create_mention_notification(
                mentioned_username, mentioned_by_user_id, notice, NotificationType.reply
            )

        # Create notifications for each mentioned user
        for mentioned_username in mentioned_usernames:
            if mentioned_username in mentioned_usernames_by_system:
                continue  # Skip if the username is already mentioned by the system

            if mentioned_by == mentioned_username:
                continue  # Skip if the user mentioned themselves

            notice = {
                # Post ID where the user was mentioned
                "post_id": post_id,
                # Username of the user who mentioned them
                "mentioned_by": mentioned_by,
                # Text of the notification, e.g., "Alice mentioned you in a post."
                "alert": f"{mentioned_by} mentioned you in a reply.",
                "text": text[150]
                if len(text) > 150
                else text,  # Short preview of the text
            }
            create_mention_notification(
                mentioned_username,
                mentioned_by_user_id,
                notice,
                NotificationType.mention,
            )

    except Exception as e:
        Log.critical(str(e))
        raise Exception(str(e))
    finally:
        session.close()


def follow(user_id: int, follower_user_id: int) -> None:
    session = SessionLocal()
    try:
        user = session.query(Users).filter(Users.id == follower_user_id).first()
        if user is None:
            return
        notic = {
            "user": user.username,
            "alert": "New follower",
            "text": f"{user.username} started following you.",
        }
        _create_notification(user_id, notic, NotificationType.follow)
    except Exception as e:
        Log.critical(str(e))
        raise Exception(str(e))
    finally:
        session.close()


def like(post_id: int, session_user_id: int) -> None:
    session = SessionLocal()
    try:
        user = session.query(Users).filter(Users.id == session_user_id).first()
        if user is None:
            return

        post = session.query(Posts).filter(Posts.id == post_id).first()
        if post is None:
            return
        preview_text = ""
        if post.text is not None:
            if len(post.text) > 150:
                preview_text = post.text[150]
        notic = {
            # Username of who liked the post
            "user": user.username,
            # alert message
            "alert": f"{user.username} liked your post.",
            # Post content text
            "text": preview_text,  # Short preview of the text,
            # post id of the post
            "post_id": post_id,
        }
        _create_notification(post.user_id, notic, NotificationType.like)
    except Exception as e:
        Log.critical(str(e))
        raise Exception(str(e))
    finally:
        session.close()


def warning(text: str) -> None:
    # TODO: Implement the warning notification logic
    notice = {
        "text": text,
    }


def danger(text: str) -> None:
    # TODO: Implement the danger notification logic
    notice = {
        "text": text,
    }


def system_update(text: str) -> None:
    # TODO: Implement the system update notification logic
    notice = {
        "text": text,
    }
