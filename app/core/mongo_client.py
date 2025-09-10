"""
MongoDB client configuration and utilities for AI Startup Copilot.
"""

import logging
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo import MongoClient
from pymongo.database import Database

from app.core.config import settings

logger = logging.getLogger(__name__)

# Global async client instance
_async_client: Optional[AsyncIOMotorClient] = None
_sync_client: Optional[MongoClient] = None


async def get_async_mongo_client() -> AsyncIOMotorClient:
    """
    Get or create an async MongoDB client using Motor.
    
    This is the preferred client for FastAPI endpoints.
    
    Returns:
        AsyncIOMotorClient: The async MongoDB client
    """
    global _async_client
    
    if _async_client is None:
        try:
            _async_client = AsyncIOMotorClient(
                settings.MONGO_URI,
                serverSelectionTimeoutMS=5000,  # 5 second timeout
                connectTimeoutMS=10000,  # 10 second timeout
                socketTimeoutMS=20000,   # 20 second timeout
                maxPoolSize=50,
                minPoolSize=5
            )
            
            # Test the connection
            await _async_client.admin.command('ping')
            logger.info("✅ Async MongoDB connection established")
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to MongoDB: {e}")
            raise
    
    return _async_client


def get_sync_mongo_client() -> MongoClient:
    """
    Get or create a synchronous MongoDB client using PyMongo.
    
    This is used for Celery tasks which are not async.
    
    Returns:
        MongoClient: The sync MongoDB client
    """
    global _sync_client
    
    if _sync_client is None:
        try:
            _sync_client = MongoClient(
                settings.MONGO_URI,
                serverSelectionTimeoutMS=5000,  # 5 second timeout
                connectTimeoutMS=10000,  # 10 second timeout
                socketTimeoutMS=20000,   # 20 second timeout
                maxPoolSize=50,
                minPoolSize=5
            )
            
            # Test the connection
            _sync_client.admin.command('ping')
            logger.info("✅ Sync MongoDB connection established")
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to MongoDB: {e}")
            raise
    
    return _sync_client


async def get_async_database() -> AsyncIOMotorDatabase:
    """
    Get the async database instance.
    
    Returns:
        AsyncIOMotorDatabase: The database instance
    """
    client = await get_async_mongo_client()
    return client[settings.MONGO_DB_NAME]


def get_sync_database() -> Database:
    """
    Get the sync database instance.
    
    Returns:
        Database: The database instance
    """
    client = get_sync_mongo_client()
    return client[settings.MONGO_DB_NAME]


async def close_async_mongo_client():
    """Close the async MongoDB client."""
    global _async_client
    if _async_client:
        _async_client.close()
        _async_client = None
        logger.info("🔒 Async MongoDB client closed")


def close_sync_mongo_client():
    """Close the sync MongoDB client."""
    global _sync_client
    if _sync_client:
        _sync_client.close()
        _sync_client = None
        logger.info("🔒 Sync MongoDB client closed")


async def create_indexes():
    """
    Create necessary database indexes for optimal performance.
    """
    try:
        db = await get_async_database()
        
        # Create indexes for the startup_profiles collection
        profiles_collection = db.startup_profiles
        
        # Index on company_url for fast lookups
        await profiles_collection.create_index("company_url", unique=True)
        
        # Index on company_name for searches
        await profiles_collection.create_index("company_name")
        
        # Index on created_at for sorting
        await profiles_collection.create_index("created_at")
        
        # Index on status for filtering
        await profiles_collection.create_index("status")
        
        # Compound index for common queries
        await profiles_collection.create_index([
            ("company_name", 1),
            ("created_at", -1)
        ])
        
        logger.info("✅ MongoDB indexes created successfully")
        
    except Exception as e:
        logger.error(f"❌ Failed to create MongoDB indexes: {e}")
        raise


async def health_check() -> dict:
    """
    Perform a health check on the MongoDB connection.
    
    Returns:
        dict: Health check result
    """
    try:
        client = await get_async_mongo_client()
        
        # Ping the server
        result = await client.admin.command('ping')
        
        # Get server info
        server_info = await client.admin.command('serverStatus')
        
        return {
            "status": "healthy",
            "ping_result": result,
            "version": server_info.get("version", "unknown"),
            "uptime": server_info.get("uptime", 0),
            "connections": server_info.get("connections", {})
        }
        
    except Exception as e:
        logger.error(f"MongoDB health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }
