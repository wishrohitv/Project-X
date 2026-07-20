import sys

import redis
from modules import create_engine, os, sessionmaker
from redis import RedisError
from settings import Settings
from utils import Logging

Log = Logging(__name__)


try:
    # Initialize database engine
    engine = create_engine(Settings.DB_URL or "", pool_pre_ping=True)

    SessionLocal = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
    )

    Log.info(f"Database engine initialized ({engine.name})")
    # Initialize Redis client
    redis_client = redis.Redis.from_url(Settings.REDIS_URL, decode_responses=True)
    Log.info(f"Redis client initialized Ping: {redis_client.ping()}")
    Log.info(f"Redis client initialized ACL: {redis_client.acl_whoami()}")
except RedisError as e:
    Log.error(f"Failed to initialize Redis client: {e}")
    sys.exit(1)
except Exception as e:
    Log.error(f"Failed to initialize database client: {e}")
    sys.exit(1)


def initialize_db():
    from models import Base

    Log.info("Creating all tables if not exists")
    # Create all tables in the engine
    Base.metadata.create_all(engine)
