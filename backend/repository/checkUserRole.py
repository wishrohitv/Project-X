from models import Accessibility, Endpoint
from modules import json, select, sessionmaker


def getUserRole(endpoint: str, userRole: int | None = None) -> bool:
    from database import engine

    Session = sessionmaker(bind=engine)
    session = Session()

    getRole = (
        select(
            Accessibility.endpointID,
            Accessibility.roles,
            Accessibility.partialAccess,
            Endpoint.endpoint,
            Endpoint.methods,
        )
        .join_from(Accessibility, Endpoint)
        .where(Endpoint.endpoint.__eq__(endpoint))
    )
    accessibilityRule = session.execute(getRole).all()

    # check if accessibilityRule not null
    if accessibilityRule:
        # accessibilityRule -> [(15, [1, 2, 3], False, '/posts/uploadPosts', ['POST'])]
        _partialAccess: bool = accessibilityRule[0][2]
        _userRole: list[int] = accessibilityRule[0][1]
        if userRole in _userRole:
            return True
        else:
            return False

    else:
        return False
