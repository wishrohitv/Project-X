from config import API_ENDPOINTS, ROLE
from database import engine
from models import Accessibility, Category, Endpoint, Role
from modules import sessionmaker

Session = sessionmaker(bind=engine)
session = Session()


# Setup initial data in database
def init_db_setup():
    check_role = session.query(Role).all()

    # Check if db has role or not then add role
    if len(check_role) == 0:
        role_obj_list = []
        for role, roleId in ROLE().roles.items():
            role_obj_list.append(Role(id=roleId, role=role))

        session.add_all(role_obj_list)
        session.commit()
        session.close()

    # _______________ Add initial endpoints
    check_endpoint = session.query(Endpoint).all()
    # Check if db has endpoints or not then add
    if len(check_endpoint) == 0:
        endpoint_obj_list = []
        for endpoint, routeAccess in API_ENDPOINTS().api_endpoints.items():
            endpoint_obj_list.append(
                Endpoint(endpoint=endpoint, methods=routeAccess.methods)
            )

        session.add_all(endpoint_obj_list)
        session.commit()
        session.close()

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
        session.close()

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
        session.close()
