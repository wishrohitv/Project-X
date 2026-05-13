from models import Accessibility, Endpoint
from modules import json, select, sessionmaker


def get_user_role(endpoint: str, user_role: int | None = None) -> bool:
    from database import engine

    Session = sessionmaker(bind=engine)
    session = Session()

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
