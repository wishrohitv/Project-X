from config import API_ENDPOINTS, ROLE
from database import SessionLocal
from models import Accessibility, Category, Endpoint, Profile, Role, Users
from modules import json, secrets
from utils import return_hashed_bytes


# Setup initial data in database
def init_db_setup():
    session = SessionLocal()
    check_role = session.query(Role).all()

    # Check if db has role or not then add role
    if len(check_role) == 0:
        role_obj_list = []
        for role, roleId in ROLE().roles.items():
            role_obj_list.append(Role(id=roleId, role=role))

        session.add_all(role_obj_list)
        session.commit()

    # _______________ Add initial endpoints
    check_endpoint = session.query(Endpoint).all()
    # Check if db has endpoints or not then add
    if len(check_endpoint) == 0:
        endpoint_obj_list = []
        for endpoint, routeAccess in API_ENDPOINTS().api_endpoints.items():
            endpoint_obj_list.append(
                Endpoint(endpoint=routeAccess.route_name, methods=routeAccess.methods)
            )

        session.add_all(endpoint_obj_list)
        session.commit()

    # _______________
    # Add accessibility in database
    check_accessibility = session.query(Accessibility).all()

    # check if db has accessibility or not then add
    if len(check_accessibility) == 0:
        access_obj_list = []
        for role_id, routeAccess in enumerate(API_ENDPOINTS().api_endpoints.values()):
            access_obj_list.append(
                Accessibility(
                    endpoint_id=role_id + 1,
                    roles=routeAccess.role_permission,
                    partial_access=routeAccess.partial_access,
                )
            )

        session.add_all(access_obj_list)
        session.commit()

    # _______________
    check_category = session.query(Category).all()

    # Check if db has categories or not then add
    if len(check_category) == 0:
        cat_obj_list = []
        for category in [
            "Politcs",
            "Reletable",
            "Troll",
            "Coding",
            "Programming",
            "Movies",
            "Sad",
            "Casual",
            "Trending",
        ]:
            cat_obj_list.append(Category(category=category))

        session.add_all(cat_obj_list)
        session.commit()

    # Add initial users
    check_users = session.query(Users).limit(1).all()

    if len(check_users) == 0:
        user_obj_list = []
        with open("./data/users.json", encoding="utf-8") as f:
            users: dict = json.load(f)
            for key, user in users.items():
                user_obj_list.append(
                    Users(
                        username=user["username"],
                        email=user["email"],
                        password= return_hashed_bytes(user["password"]) if user["password"] else secrets.token_bytes(16),
                        role=user["role"],
                        is_verified=user["is_verified"],
                        name=user.get("name") or "",
                        profile=Profile(
                            bio=user.get("bio") or "",
                            country=user.get("country") or "",
                        ),
                    )
                )

        session.add_all(user_obj_list)
        session.commit()

    session.close()
