from models import Accessibility, AccountStatus, Endpoint, Users
from modules import json, select
from utils import AppError, ForbiddenError, InternalServerError, ResourceNotFoundError


def get_user_role(endpoint: str, user_id: int, user_role: int) -> bool:
    from database import SessionLocal

    session = SessionLocal()

    try:
        user = session.query(Users).where(Users.id == user_id).first()
        session.close()
        if user:
            if user.account_status == AccountStatus.banned:
                raise ForbiddenError("Account is banned")
            if user.account_status == AccountStatus.suspended:
                raise ForbiddenError("Account is suspended")
            if user.account_status == AccountStatus.deleted:
                raise ForbiddenError("Account is deleted")
        else:
            raise ResourceNotFoundError("Account not found")

        # Check user role
        # TODO: match user endpoint along with request method
        get_role = (
            select(
                Accessibility.endpoint_id,
                Accessibility.roles,
                Accessibility.partial_access,
                Endpoint.endpoint,
                Endpoint.methods,
            )
            .join_from(Accessibility, Endpoint)
            .where(Endpoint.endpoint.__eq__(endpoint))
        )
        accessibility_rule = session.execute(get_role).all()

        # check if accessibility_rule not null
        if accessibility_rule:
            # accessibility_rule -> [(15, [1, 2, 3], False, '/posts/uploadPosts', ['POST'])]
            _partial_access: bool = accessibility_rule[0][2]
            _user_role: list[int] = accessibility_rule[0][1]
            if user_role in _user_role:
                return True
            else:
                return False

        else:
            return False
    except AppError:
        raise
    except Exception as e:
        raise InternalServerError("Error while user token") from e

    finally:
        session.close()
