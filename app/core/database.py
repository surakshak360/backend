from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from neo4j import AsyncGraphDatabase, AsyncDriver
import redis.asyncio as aioredis
from app.core.config import settings
from app.core.logging import logger


class Database:
    client: Optional[AsyncIOMotorClient] = None
    db: Optional[AsyncIOMotorDatabase] = None
    neo4j_driver: Optional[AsyncDriver] = None
    redis_client: Optional[aioredis.Redis] = None


db_instance = Database()


async def connect_to_mongo():
    logger.info("Connecting to MongoDB...", uri=settings.MONGODB_URI)
    try:
        db_instance.client = AsyncIOMotorClient(
            settings.MONGODB_URI,
            serverSelectionTimeoutMS=500
        )
        # Verify server is reachable
        await db_instance.client.admin.command('ping')
        db_instance.db = db_instance.client[settings.MONGODB_DB_NAME]
        logger.info("Connected to MongoDB", db_name=settings.MONGODB_DB_NAME)
    except Exception as e:
        logger.warning("MongoDB not reachable, running in mock/fallback mode", error=str(e))
        db_instance.client = None
        db_instance.db = None


async def close_mongo_connection():
    if db_instance.client:
        logger.info("Closing MongoDB connection...")
        db_instance.client.close()
        logger.info("MongoDB connection closed.")


async def connect_to_neo4j():
    try:
        logger.info("Connecting to Neo4j...", uri=settings.NEO4J_URI)
        db_instance.neo4j_driver = AsyncGraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
        )
        logger.info("Connected to Neo4j driver")
    except Exception as e:
        logger.warning("Neo4j connection deferred or failed", error=str(e))


async def close_neo4j_connection():
    if db_instance.neo4j_driver:
        logger.info("Closing Neo4j driver...")
        await db_instance.neo4j_driver.close()


async def connect_to_redis():
    try:
        logger.info("Connecting to Redis...", url=settings.REDIS_URL)
        db_instance.redis_client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
        logger.info("Connected to Redis")
    except Exception as e:
        logger.warning("Redis connection deferred or failed", error=str(e))


async def close_redis_connection():
    if db_instance.redis_client:
        logger.info("Closing Redis client...")
        await db_instance.redis_client.aclose()


def get_mongo_db() -> AsyncIOMotorDatabase:
    return db_instance.db


def get_neo4j_session():
    """Context manager yielding an async Neo4j session. Returns None if driver unavailable."""
    if db_instance.neo4j_driver is None:
        return None
    return db_instance.neo4j_driver.session()


def get_redis():
    """Return the Redis async client, or None if unavailable."""
    return db_instance.redis_client
