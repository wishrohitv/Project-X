from database import engine
from models import Users
from models.enums import NotificationType
from modules import sessionmaker
from repository.notificationRepository import _createNotification
from utils import Log, get_user_names

Session = sessionmaker(bind=engine)
session = Session()


def mention(
    mentionedByUserID: int,
    postID: int,
    text: str,
) -> None | Exception:
    try:
        # Extract mentioned usernames from the text
        mentionedUsernames = getUsername(text)

        # Get the username of the user who mentioned others
        result = (
            session.query(Users.userName).filter(Users.id == mentionedByUserID).first()
        )
        # Get the username of the user who mentioned others
        mentionedBy = result[0] if result else None

        # If the user who mentioned others is not found, we can't create notifications
        if not mentionedBy:
            return

        # Create notifications for each mentioned user
        for mentionedUsername in mentionedUsernames:
            # Find the user ID of the mentioned username
            result = (
                session.query(Users.id)
                .filter(Users.userName == mentionedUsername)
                .first()
            )
            # User iD of the mentioned user, if found, else None
            userID = result[0] if result else None

            # If the mentioned user is found, create a notification for them
            if userID:
                notice = {
                    # Post ID where the user was mentioned
                    "postID": postID,
                    # Username of the user who mentioned them
                    "mentionedBy": mentionedBy,
                    # Text of the notification, e.g., "Alice mentioned you in a post."
                    "alert": f"{mentionedBy} mentioned you in a post.",
                    "text": text[150]
                    if len(text) > 150
                    else text,  # Short preview of the text
                }
                # Create the notification using the createNotification function
                _createNotification(
                    userID=userID,
                    notice=notice,
                    type=NotificationType.mention,
                )
    except Exception as e:
        session.close()
        Log.critical(str(e))
        raise Exception(str(e))


def suggestion(
    postID: int,
    userID: list[int],  # list of user IDs to whom the suggestion is made
    text: str,  # title of the post or ""
) -> None | Exception:
    notice = {
        "postID": postID,
        "text": text[150] if len(text) > 150 else text,  # Short preview of the text,
    }

    for _userID in userID:
        # Create the notification using the createNotification function
        _createNotification(
            userID=_userID,
            notice=notice,
            type=NotificationType.suggestion,
        )


def reply(
    parentPostID: int,
    postID: int,
    mentionedUsernamesBySystem: list[
        str
    ],  # list of usernames mentioned by system in the reply in the thread
    mentionedByUserID: int,  # user ID of post/reply author who mentioned others in the thread
    text: str,  # title of the post or ""
) -> None | Exception:
    try:

        def createMentionNotification(
            mentionedUsername: str,
            _userID: int,
            _notice: dict,
            type: NotificationType,
        ):
            # Find the user ID of the mentioned username
            result = (
                session.query(Users.id)
                .filter(Users.userName == mentionedUsername)
                .first()
            )
            # User iD of the mentioned user, if found, else None
            userID = result[0] if result else None

            # If the mentioned user is found, create a notification for them
            if userID:
                # Create the notification using the createNotification function
                _createNotification(
                    userID=_userID,
                    notice=_notice,
                    type=type,
                )

        # Extract mentioned usernames from the text
        mentionedUsernames = getUsername(text)

        # Get the username of the user who mentioned others
        result = (
            session.query(Users.userName).filter(Users.id == mentionedByUserID).first()
        )
        # Get the username of the user who mentioned others
        mentionedBy = result[0] if result else None

        # If the user who mentioned others is not found, we can't create notifications
        if not mentionedBy:
            return

        # Create notifications for each mentioned user by the system (e.g., if the system automatically mentions users in a thread)
        for mentionedUsername in mentionedUsernamesBySystem:
            if mentionedBy == mentionedUsername:
                continue  # Skip if the user mentioned themselves

            notice = {
                # Post ID where the user was mentioned
                "postID": postID,
                # Username of the user who mentioned them
                "mentionedBy": mentionedBy,
                # Text of the notification, e.g., "Alice mentioned you in a post."
                "alert": f"{mentionedBy} is replied you.",
                "text": text[150]
                if len(text) > 150
                else text,  # Short preview of the text
            }
            createMentionNotification(
                mentionedUsername, mentionedByUserID, notice, NotificationType.reply
            )

        # Create notifications for each mentioned user
        for mentionedUsername in mentionedUsernames:
            if mentionedUsername in mentionedUsernamesBySystem:
                continue  # Skip if the username is already mentioned by the system

            if mentionedBy == mentionedUsername:
                continue  # Skip if the user mentioned themselves

            notice = {
                # Post ID where the user was mentioned
                "postID": postID,
                # Username of the user who mentioned them
                "mentionedBy": mentionedBy,
                # Text of the notification, e.g., "Alice mentioned you in a post."
                "alert": f"{mentionedBy} mentioned you in a reply.",
                "text": text[150]
                if len(text) > 150
                else text,  # Short preview of the text
            }
            createMentionNotification(
                mentionedUsername,
                mentionedByUserID,
                notice,
                NotificationType.mention,
            )

    except Exception as e:
        session.close()
        Log.critical(str(e))
        raise Exception(str(e))


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


def systemUpdate(text: str) -> None:
    # TODO: Implement the system update notification logic
    notice = {
        "text": text,
    }
