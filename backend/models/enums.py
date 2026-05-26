from modules import PyEnum


# Post's age ratings
class AgeRating(PyEnum.Enum):
    pg13 = "pg13"
    nsfw = "NSFW"


# Account's status
class AccountStatus(PyEnum.Enum):
    active = "active"
    suspended = "suspended"
    banned = "banned"
    deleted = "deleted"


# Notifications types
class NotificationType(PyEnum.Enum):
    mention = "mention"
    suggestion = "suggestion"  # Recommendation of post
    reply = "reply"
    warning = "warning"
    danger = "danger"
    systemUpdate = "system_update"
    follow = "follow"


# OAuth providers
class OAuthProvider(PyEnum.Enum):
    local = "local"
    google = "google"
    x = "x"
    discord = "discord"
    apple = "apple"
