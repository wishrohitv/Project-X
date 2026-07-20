from database import redis_client
from modules import request
from utils import RateLimitExceededError, RouteAccess


def rate_limiter_middleware(
    route: RouteAccess, limit: int = 5, period: int = 60, exponential: bool = False
):
    """
    Rate limiter middleware that limits the number of requests to a given endpoint.
    Defaults to 5 requests per 60 seconds.
    Args:
        endpoint (str): The endpoint to rate limit.
        limit (int): The maximum number of requests allowed within the period.
        period (int): The time period in seconds for the rate limit.
    """

    def route_funtion(func):
        def wrapper(*args, **kwargs):
            key = f"rate_limit_endpoint:{route.route_name}:{request.remote_addr}"
            count = redis_client.incr(key)
            if count == 1:
                redis_client.expire(key, period)
            if int(count) > limit:
                raise RateLimitExceededError()
            return func(*args, **kwargs)

        return wrapper

    return route_funtion
