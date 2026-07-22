from database import redis_client
from modules import functools, request
from settings import Settings
from utils import RateLimitExceededError, RouteAccess


def rate_limiter_middleware(
    route: RouteAccess, limit: int = 5, period: int = 60, exponential: bool = False
):
    """
    Rate limiter middleware that limits the number of requests to a given endpoint.
    Defaults to 5 requests per 60 seconds.
    Args:
        route (RouteAccess): The endpoint to rate limit.
        limit (int): The maximum number of requests allowed within the period.
        period (int): The time period in seconds for the rate limit.
        exponential (bool): Whether to use exponential backoff for rate limiting.
    """

    def route_funtion(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            key = f"rate_limit_endpoint:{request.path}:{request.remote_addr}"
            count = redis_client.incr(key)
            ttl = redis_client.ttl(key)
            if count == 1:
                redis_client.expire(key, period)
            if int(count) > limit:
                if exponential:
                    redis_client.expire(key, ttl + period)
                raise RateLimitExceededError(
                    f"Rate limit exceeded for endpoint {request.path if Settings.DEBUG else ''}, try after {redis_client.ttl(key)} seconds"
                )
            return func(*args, **kwargs)

        return wrapper

    return route_funtion
