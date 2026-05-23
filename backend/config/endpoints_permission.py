from utils.data_models.route_access import RouteAccess

from config.roles import ROLE


class API_ENDPOINTS:
    """
    Role of users who can access api endpoints based on their role
    defined here
    """

    # Auth
    auth_signup = RouteAccess(
        # Signup user
        route_name="/auth/signup",
        methods=["POST"],
        role_permission=[],
    )
    auth_login = RouteAccess(
        # Login user
        route_name="/auth/login",
        role_permission=[ROLE.SUPER_ADMIN, ROLE.MODERATOR, ROLE.USER],
        methods=["POST"],
        partial_access=True,
    )
    auth_logout = RouteAccess(
        # Logout user
        route_name="/auth/logout",
        role_permission=[ROLE.SUPER_ADMIN, ROLE.MODERATOR, ROLE.USER],
        methods=["POST"],
    )
    auth_refresh = RouteAccess(
        # Refresh token
        route_name="/auth/refresh",
        role_permission=[ROLE.SUPER_ADMIN, ROLE.MODERATOR, ROLE.USER],
        methods=["POST"],
    )
    auth_generate_otp = RouteAccess(
        # Generate otp for verification
        route_name="/auth/otp/generate",
        role_permission=[ROLE.SUPER_ADMIN, ROLE.MODERATOR, ROLE.USER],
        methods=["POST"],
        partial_access=True,
    )
    auth_verify_otp = RouteAccess(
        # Verify otp
        route_name="/auth/otp/verify",
        role_permission=[ROLE.SUPER_ADMIN, ROLE.MODERATOR, ROLE.USER],
        methods=["POST"],
        partial_access=True,
    )
    auth_current_user = RouteAccess(
        # Get current session user
        route_name="/auth/c/user",  # session user only
        role_permission=[ROLE.SUPER_ADMIN, ROLE.MODERATOR, ROLE.USER],
        methods=["GET"],
    )

    # User route
    user_delete = RouteAccess(
        # Delete user account
        route_name="/users",
        role_permission=[ROLE.SUPER_ADMIN, ROLE.MODERATOR, ROLE.USER],
        methods=["DELETE"],
    )
    user_suspend = RouteAccess(
        # Suspend user account
        route_name="/users/<int:user_id>/suspend",
        role_permission=[ROLE.MODERATOR, ROLE.SUPER_ADMIN],
        methods=["POST"],
    )
    user = RouteAccess(
        # Get user profile
        route_name="/users/<string:username>",
        role_permission=[ROLE.SUPER_ADMIN, ROLE.MODERATOR, ROLE.USER, ROLE.GUEST],
        methods=["GET"],
        partial_access=True,
    )
    user_update = RouteAccess(
        route_name="/users",
        role_permission=[ROLE.SUPER_ADMIN, ROLE.MODERATOR, ROLE.USER],
        methods=["PUT"],
    )
    user_change_profile = RouteAccess(
        # Update profile image
        route_name="/users/profile_img",
        role_permission=[ROLE.SUPER_ADMIN, ROLE.MODERATOR, ROLE.USER],
        methods=["PUT"],
    )
    user_ban_user = RouteAccess(
        # Ban a user
        route_name="/users/<int:user_id>/ban",
        role_permission=[ROLE.SUPER_ADMIN],
        methods=["POST"],
    )
    user_unban_user = RouteAccess(
        # Unban a user
        route_name="/users/<int:user_id>/ban",
        role_permission=[ROLE.SUPER_ADMIN],
        methods=["PUT"],
    )
    user_add_follower = RouteAccess(
        # Follow a user
        route_name="/users/<int:user_id>/follow",
        role_permission=[ROLE.USER],
        methods=["POST"],
    )
    user_remove_follower = RouteAccess(
        # Unfollow a user
        route_name="/users/<int:user_id>/follow",
        role_permission=[ROLE.USER],
        methods=["DELETE"],
    )
    user_block = RouteAccess(
        # Block a user
        route_name="/users/<int:user_id>/block",
        role_permission=[ROLE.USER],
        methods=["POST"],
    )
    user_unblock = RouteAccess(
        # Unblock a user
        route_name="/users/<int:user_id>/block",
        role_permission=[ROLE.USER],
        methods=["DELETE"],
    )
    user_report_users = RouteAccess(
        # Report a user
        route_name="/users/<int:user_id>/report",
        role_permission=[ROLE.USER],
        methods=["POST"],
    )
    user_report_inspector = RouteAccess(
        # TODO: Inspect a reported user
        route_name="/users/<int:report_id>/report-inspector",
        role_permission=[ROLE.SUPER_ADMIN, ROLE.MODERATOR],
        methods=["PUT"],
    )

    # Feed
    feed = RouteAccess(
        route_name="/feed",
        role_permission=[ROLE.SUPER_ADMIN, ROLE.MODERATOR, ROLE.USER],
        methods=["GET"],
        partial_access=True,
    )
    # Profile
    profile_image_upload = RouteAccess(
        route_name="/users/profile/image",
        methods=["POST"],
        role_permission=[ROLE.SUPER_ADMIN, ROLE.MODERATOR, ROLE.USER],
    )
    profile_image_get = RouteAccess(
        route_name="/users/profile/image",
        role_permission=[ROLE.SUPER_ADMIN, ROLE.MODERATOR, ROLE.USER],
        methods=["GET"],
        partial_access=True,
    )
    profile_image_update = RouteAccess(
        route_name="/users/profile/image",
        role_permission=[ROLE.SUPER_ADMIN, ROLE.MODERATOR, ROLE.USER],
        methods=["PUT"],
    )
    profile_image_delete = RouteAccess(
        route_name="/users/profile/image",
        role_permission=[ROLE.SUPER_ADMIN, ROLE.MODERATOR, ROLE.USER],
        methods=["DELETE"],
    )
    # Posts
    posts = RouteAccess(
        route_name="/posts/<string:username>",
        role_permission=[ROLE.SUPER_ADMIN, ROLE.MODERATOR, ROLE.USER],
        methods=["GET"],
        partial_access=True,
    )
    # Posts by Id
    posts_by_id = RouteAccess(
        route_name="/posts/<int:post_id>",
        role_permission=[ROLE.SUPER_ADMIN, ROLE.MODERATOR, ROLE.USER],
        methods=["GET"],
        partial_access=True,
    )
    posts_liked_users = RouteAccess(
        # Users who liked the post
        route_name="/posts/<int:post_id>/liked-users",
        role_permission=[ROLE.SUPER_ADMIN, ROLE.MODERATOR, ROLE.USER],
        methods=["GET"],
        partial_access=True,
    )
    post_bookmarked_users = RouteAccess(
        # Users who bookmarked the post
        route_name="/posts/<int:post_id>/bookmarked-users",  # This could be privacy voilation of user who bookmarked the post, make partial access false
        role_permission=[ROLE.SUPER_ADMIN, ROLE.MODERATOR, ROLE.USER],
        methods=["GET"],
        partial_access=True,
    )
    post_reposted_users = RouteAccess(
        # Reposted users of the post
        route_name="/posts/<int:post_id>/reposted-users",
        role_permission=[ROLE.SUPER_ADMIN, ROLE.MODERATOR, ROLE.USER],
        methods=["GET"],
        partial_access=True,
    )
    post_qouted_users = RouteAccess(
        # Qouted users of the post
        route_name="/posts/<int:post_id>/qouted-users",
        role_permission=[ROLE.SUPER_ADMIN, ROLE.MODERATOR, ROLE.USER],
        methods=["GET"],
        partial_access=True,
    )
    post_upload_post = RouteAccess(
        # Upload a post
        route_name="/posts",
        role_permission=[ROLE.SUPER_ADMIN, ROLE.MODERATOR, ROLE.USER],
        methods=["POST"],
    )
    post_repost = RouteAccess(
        # Repost a post
        route_name="/posts/<int:post_id>/repost",
        role_permission=[ROLE.SUPER_ADMIN, ROLE.MODERATOR, ROLE.USER],
        methods=["POST"],
    )
    post_repost_undo = RouteAccess(
        # Undo repost of a post
        route_name="/posts/<int:post_id>/repost",
        role_permission=[ROLE.SUPER_ADMIN, ROLE.MODERATOR, ROLE.USER],
        methods=["DELETE"],
    )
    post_like = RouteAccess(
        # Like a post
        route_name="/posts/<int:post_id>/like",
        role_permission=[ROLE.SUPER_ADMIN, ROLE.MODERATOR, ROLE.USER],
        methods=["POST"],
    )
    post_like_undo = RouteAccess(
        # Undo like of a post
        route_name="/posts/<int:post_id>/like",
        role_permission=[ROLE.SUPER_ADMIN, ROLE.MODERATOR, ROLE.USER],
        methods=["DELETE"],
    )
    post_bookmark = RouteAccess(
        # Bookmark a post
        route_name="/posts/<int:post_id>/bookmark",
        role_permission=[ROLE.SUPER_ADMIN, ROLE.MODERATOR, ROLE.USER],
        methods=["POST"],
    )
    post_bookmark_undo = RouteAccess(
        # Undo bookmark of a post
        route_name="/posts/<int:post_id>/bookmark",
        role_permission=[ROLE.SUPER_ADMIN, ROLE.MODERATOR, ROLE.USER],
        methods=["DELETE"],
    )
    post_delete = RouteAccess(
        # Delete a post
        route_name="/posts/<int:post_id>",
        role_permission=[ROLE.SUPER_ADMIN, ROLE.MODERATOR, ROLE.USER],
        methods=["DELETE"],
    )
    post_update = RouteAccess(
        # Update a post
        route_name="/posts/<int:post_id>",
        role_permission=[ROLE.SUPER_ADMIN, ROLE.MODERATOR, ROLE.USER],
        methods=["PATCH"],
    )
    report_post = RouteAccess(
        # Report a post
        route_name="/posts/<int:post_id>/report",
        role_permission=[ROLE.SUPER_ADMIN, ROLE.MODERATOR, ROLE.USER],
        methods=["POST"],
    )
    report_post_inspector = RouteAccess(
        # TODO: Inspect a reported post
        route_name="/posts/<int:post_id>/report-inspector",
        role_permission=[ROLE.SUPER_ADMIN, ROLE.MODERATOR],
        methods=["POST"],
    )
    # Replies
    post_replies = RouteAccess(
        # Get post replies
        route_name="/posts/<int:post_id>/replies",
        role_permission=[ROLE.SUPER_ADMIN, ROLE.MODERATOR, ROLE.USER],
        methods=["GET"],
        partial_access=True,
    )
    # Mark post as meme template
    mark_as_template = RouteAccess(
        # Mark post as meme template
        route_name="/posts/<int:post_id>/template",
        role_permission=[ROLE.USER],
        methods=["PUT"],
    )
    remove_template = RouteAccess(
        route_name="/posts/<int:post_id>/template",
        role_permission=[ROLE.USER],
        methods=["DELETE"],
    )

    # Collection
    collection_list = RouteAccess(
        # Get all collections
        route_name="/collections/list/<int:user_id>",
        role_permission=[ROLE.USER, ROLE.SUPER_ADMIN, ROLE.MODERATOR],
        methods=["GET"],
    )
    collection = RouteAccess(
        # Get all collections
        route_name="/collections/<int:collection_id>",
        role_permission=[ROLE.USER, ROLE.SUPER_ADMIN, ROLE.MODERATOR],
        methods=["GET"],
    )
    collection_create = RouteAccess(
        # Create a new collection
        route_name="/collections",
        role_permission=[ROLE.USER, ROLE.SUPER_ADMIN, ROLE.MODERATOR],
        methods=["POST"],
    )
    collection_delete = RouteAccess(
        route_name="/collections/<int:collection_id>",
        role_permission=[ROLE.USER, ROLE.SUPER_ADMIN, ROLE.MODERATOR],
        methods=["DELETE"],
    )
    collection_update = RouteAccess(
        route_name="/collections/<int:collection_id>",
        role_permission=[ROLE.USER, ROLE.SUPER_ADMIN, ROLE.MODERATOR],
        methods=["PATCH"],
    )
    collection_add_post = RouteAccess(
        route_name="/collections/<int:collection_id>/<int:post_id>",
        role_permission=[ROLE.USER, ROLE.SUPER_ADMIN, ROLE.MODERATOR],
        methods=["POST"],
    )
    collection_remove_post = RouteAccess(
        route_name="/collections/<int:collection_id>/<int:post_id>",
        role_permission=[ROLE.USER, ROLE.SUPER_ADMIN, ROLE.MODERATOR],
        methods=["DELETE"],
    )
    get_notifications = RouteAccess(
        route_name="/notifications",
        role_permission=[ROLE.USER, ROLE.SUPER_ADMIN, ROLE.MODERATOR],
        methods=["GET"],
    )
    track_notifications = RouteAccess(
        route_name="/notifications/<int:notification_id>/clicked",
        role_permission=[ROLE.USER, ROLE.SUPER_ADMIN, ROLE.MODERATOR],
        methods=["PATCH"],
    )

    @property
    def api_endpoints(self) -> dict[str, RouteAccess]:
        """
        endpoint name : route name
        """
        return {
            v.route_name: v
            for k, v in self.__class__.__dict__.items()
            if isinstance(v, RouteAccess)
        }

    @property
    def api_endpoints_partial_access(self) -> dict[str, bool]:
        """
        endpoint name : access rule
        """
        return {
            v.route_name: v.partial_access
            for k, v in self.__class__.__dict__.items()
            if isinstance(v, RouteAccess)
        }
