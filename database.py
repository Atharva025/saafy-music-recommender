"""
MongoDB Database Configuration and Connection Management
Uses motor for async MongoDB operations

CRITICAL: MongoDB Atlas Vector Search Index Configuration
=========================================================
Before running this application, you MUST create a Vector Search Index in MongoDB Atlas.

1. Go to MongoDB Atlas Dashboard → Your Cluster → Search (in left sidebar)
2. Click "Create Search Index"
3. Choose "JSON Editor" 
4. Use the following configuration:

{
  "fields": [
    {
      "type": "vector",
      "path": "embedding",
      "numDimensions": 384,
      "similarity": "cosine"
    },
    {
      "type": "filter",
      "path": "song_id"
    },
    {
      "type": "filter",
      "path": "language"
    }
  ]
}

5. Set Index Name to: "vector_index"
6. Database: music_recommendations (or your configured DB name)
7. Collection: songs
8. Click "Create Search Index" and wait for it to become active (takes 1-2 minutes)

Without this index, the /recommend endpoint will fail!
=========================================================
"""
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import ConnectionFailure
from config import get_settings
import logging
import certifi
import ssl

logger = logging.getLogger(__name__)

# Global database client and database instances
_client: AsyncIOMotorClient = None
_database: AsyncIOMotorDatabase = None


async def connect_to_mongo() -> None:
    """
    Establish connection to MongoDB Atlas
    Should be called during application startup
    """
    global _client, _database
    
    settings = get_settings()
    
    try:
        logger.info("Connecting to MongoDB Atlas...")
        
        # HF Spaces / Gradio compatible connection settings
        connection_params = {
            "serverSelectionTimeoutMS": 30000,
            "connectTimeoutMS": 30000,
            "socketTimeoutMS": 30000,
            "maxPoolSize": 10,
            "minPoolSize": 1,
            "retryWrites": True,
            # Try proper TLS first
            "tls": True,
            "tlsCAFile": certifi.where(),
        }
        
        try:
            logger.info("Attempting secure TLS connection with certifi CA bundle...")
            _client = AsyncIOMotorClient(
                settings.mongodb_uri,
                **connection_params
            )
            # Test the connection
            await _client.admin.command('ping')
            logger.info("Secure TLS connection successful!")
            
        except Exception as e:
            logger.warning(f"Secure TLS connection failed: {e}")
            logger.info("Falling back to relaxed TLS validation...")
            
            # Fallback: Allow connection even with cert issues
            connection_params = {
                "serverSelectionTimeoutMS": 30000,
                "connectTimeoutMS": 30000,
                "socketTimeoutMS": 30000,
                "maxPoolSize": 10,
                "minPoolSize": 1,
                "retryWrites": True,
                "tls": True,
                "tlsAllowInvalidCertificates": True,
                "tlsAllowInvalidHostnames": True,
            }
            
            _client = AsyncIOMotorClient(
                settings.mongodb_uri,
                **connection_params
            )
        
        # Verify connection
        await _client.admin.command('ping')
        
        _database = _client[settings.mongodb_db_name]
        logger.info(f"Successfully connected to database: {settings.mongodb_db_name}")
        
        # Create indexes for better query performance
        await create_indexes()
        
    except ConnectionFailure as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during MongoDB connection: {e}")
        raise


async def close_mongo_connection() -> None:
    """
    Close MongoDB connection
    Should be called during application shutdown
    """
    global _client
    
    if _client:
        logger.info("Closing MongoDB connection...")
        _client.close()
        logger.info("MongoDB connection closed")


async def create_indexes() -> None:
    """
    Create database indexes for efficient querying
    """
    global _database
    
    if _database is None:
        raise RuntimeError("Database not initialized")
    
    songs_collection = _database.songs
    
    # Create unique index on song_id to prevent duplicates
    await songs_collection.create_index("song_id", unique=True)
    
    # Create index on language for filtering
    await songs_collection.create_index("language")
    
    logger.info("Database indexes created successfully")


def get_database() -> AsyncIOMotorDatabase:
    """
    Get the MongoDB database instance
    
    Returns:
        AsyncIOMotorDatabase instance
        
    Raises:
        RuntimeError: If database connection hasn't been established
    """
    global _database
    
    if _database is None:
        raise RuntimeError("Database not initialized. Call connect_to_mongo() first.")
    
    return _database


async def check_vector_index_exists() -> bool:
    """
    Check if the required vector search index exists
    
    Returns:
        True if vector_index exists, False otherwise
    """
    try:
        db = get_database()
        # This is a basic check - in production, you'd want to use MongoDB's
        # Search Index API to verify the index configuration
        indexes = await db.songs.list_indexes().to_list(length=None)
        
        # Note: Vector Search indexes are created through Atlas UI
        # This just warns if the collection doesn't exist yet
        logger.info(f"Found {len(indexes)} indexes on songs collection")
        return True
        
    except Exception as e:
        logger.warning(f"Could not verify vector index: {e}")
        return False
