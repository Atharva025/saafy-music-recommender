"""
FastAPI Backend Service - Intelligent Music Recommendation Proxy
Acts as middleware between frontend and Saafy API
Provides ML-powered song recommendations using vector embeddings
"""
import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Optional

import requests
from fastapi import FastAPI, HTTPException, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import get_settings
from database import (
    connect_to_mongo,
    close_mongo_connection,
    get_database,
    check_vector_index_exists,
)
from ml_engine import initialize_ml_engine, get_ml_engine
from schemas import (
    SearchResponse,
    SongDocument,
    RecommendationsListResponse,
    RecommendationResponse,
    ErrorResponse,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events
    """
    # Startup
    logger.info("Starting up application...")
    settings = get_settings()
    
    # Initialize ML Engine (loads the model)
    initialize_ml_engine(settings.model_name)
    logger.info("ML Engine initialized")
    
    # Connect to MongoDB
    await connect_to_mongo()
    logger.info("Database connected")
    
    # Verify vector index exists (just a warning, not blocking)
    await check_vector_index_exists()
    
    logger.info("Application startup complete!")
    
    yield
    
    # Shutdown
    logger.info("Shutting down application...")
    await close_mongo_connection()
    logger.info("Application shutdown complete")


# Initialize FastAPI app
app = FastAPI(
    title="Music Recommendation Backend",
    description="Intelligent proxy and recommendation engine for music streaming",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS to allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def fetch_from_saafy(endpoint: str, params: dict = None) -> dict:
    """
    Fetch data from Saafy API
    
    Args:
        endpoint: API endpoint path (e.g., "/search/songs")
        params: Query parameters
        
    Returns:
        JSON response data
        
    Raises:
        HTTPException: If API request fails
    """
    settings = get_settings()
    url = f"{settings.saafy_api_base_url}{endpoint}"
    
    try:
        logger.info(f"Fetching from Saafy API: {url} with params: {params}")
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logger.error(f"Saafy API request failed: {e}")
        raise HTTPException(
            status_code=502,
            detail=f"Failed to fetch data from Saafy API: {str(e)}"
        )


async def process_and_store_song(song_data: dict) -> None:
    """
    Process a song: generate embedding and store in MongoDB
    Runs as a background task to avoid blocking the response
    
    Args:
        song_data: Raw song data from Saafy API
    """
    try:
        song_id = song_data.get("id")
        
        if not song_id:
            logger.warning("Song data missing ID, skipping")
            return
        
        db = get_database()
        songs_collection = db.songs
        
        # Check if song already exists
        existing = await songs_collection.find_one({"song_id": song_id})
        if existing:
            logger.debug(f"Song {song_id} already exists in database")
            return
        
        # Extract relevant fields
        name = song_data.get("name", "Unknown")
        language = song_data.get("language", "")
        
        # Extract primary artist
        artists = song_data.get("artists", {})
        primary_artists = artists.get("primary", [])
        primary_artist = primary_artists[0].get("name") if primary_artists else "Unknown"
        
        # Extract album name
        album = song_data.get("album", {})
        album_name = album.get("name", "") if album else ""
        
        # Create text for embedding
        ml_engine = get_ml_engine()
        song_text = ml_engine.create_song_text(
            name=name,
            artist=primary_artist,
            album=album_name,
            language=language
        )
        
        # Generate embedding
        logger.info(f"Generating embedding for song: {name} by {primary_artist}")
        embedding = ml_engine.generate_embedding(song_text)
        
        # Create document
        song_doc = SongDocument(
            song_id=song_id,
            name=name,
            language=language,
            primary_artist=primary_artist,
            album_name=album_name,
            embedding=embedding,
            raw_data=song_data
        )
        
        # Insert into MongoDB
        await songs_collection.insert_one(song_doc.model_dump())
        logger.info(f"Successfully stored song: {song_id} - {name}")
        
    except Exception as e:
        logger.error(f"Error processing song: {e}", exc_info=True)


async def ingest_songs_background(songs: list) -> None:
    """
    Process multiple songs in the background
    
    Args:
        songs: List of song data dictionaries
    """
    tasks = [process_and_store_song(song) for song in songs]
    await asyncio.gather(*tasks, return_exceptions=True)


# ============================================================================
# API ROUTES
# ============================================================================

@app.get("/", tags=["Health"])
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Music Recommendation Backend",
        "version": "1.0.0"
    }


@app.get("/proxy/search", tags=["Proxy"])
async def proxy_search(
    background_tasks: BackgroundTasks,
    query: str = Query(..., description="Search query string"),
    page: int = Query(0, description="Page number"),
    limit: int = Query(10, description="Results per page")
):
    """
    Proxy endpoint for song search
    
    Forwards search request to Saafy API, triggers background ingestion,
    and returns results immediately to frontend.
    
    Args:
        query: Search query string
        page: Page number for pagination
        limit: Number of results per page
        
    Returns:
        Search results from Saafy API
    """
    try:
        # Fetch from Saafy API
        params = {"query": query, "page": page, "limit": limit}
        data = fetch_from_saafy("/search/songs", params)
        
        # Extract songs from response
        if data.get("success") and data.get("data"):
            songs = data["data"].get("results", [])
            
            if songs:
                # Trigger background ingestion (non-blocking)
                background_tasks.add_task(ingest_songs_background, songs)
                logger.info(f"Queued {len(songs)} songs for background processing")
        
        # Return data immediately to frontend
        return data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in proxy_search: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get(
    "/recommend/{song_id}",
    response_model=RecommendationsListResponse,
    responses={404: {"model": ErrorResponse}},
    tags=["Recommendations"]
)
async def get_recommendations(
    song_id: str,
    limit: int = Query(10, ge=1, le=50, description="Number of recommendations")
):
    """
    Get song recommendations based on vector similarity
    
    Uses MongoDB Atlas Vector Search to find songs with similar embeddings
    to the query song.
    
    Args:
        song_id: ID of the song to get recommendations for
        limit: Maximum number of recommendations to return
        
    Returns:
        List of similar songs with similarity scores
        
    Raises:
        404: If song hasn't been analyzed yet (not in database)
        500: If vector search fails
    """
    try:
        db = get_database()
        songs_collection = db.songs
        
        # Find the query song
        query_song = await songs_collection.find_one({"song_id": song_id})
        
        if not query_song:
            raise HTTPException(
                status_code=404,
                detail=f"Song not analyzed yet. Please search for this song first to generate its embedding."
            )
        
        # Extract embedding
        query_embedding = query_song.get("embedding")
        
        if not query_embedding:
            raise HTTPException(
                status_code=500,
                detail="Song embedding not found in database"
            )
        
        # Perform vector search using MongoDB Atlas Vector Search
        # This requires the vector index to be created in Atlas (see database.py)
        pipeline = [
            {
                "$vectorSearch": {
                    "index": "vector_index",  # Must match the index name in Atlas
                    "path": "embedding",
                    "queryVector": query_embedding,
                    "numCandidates": limit * 10,  # Search more candidates for better results
                    "limit": limit + 1,  # +1 to exclude the query song itself
                }
            },
            {
                "$project": {
                    "song_id": 1,
                    "name": 1,
                    "primary_artist": 1,
                    "album_name": 1,
                    "language": 1,
                    "raw_data": 1,
                    "score": {"$meta": "vectorSearchScore"}
                }
            }
        ]
        
        # Execute aggregation pipeline
        try:
            cursor = songs_collection.aggregate(pipeline)
            results = await cursor.to_list(length=limit + 1)
        except Exception as e:
            logger.error(f"Vector search failed: {e}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail="Vector search failed. Ensure vector index is created in MongoDB Atlas."
            )
        
        # Filter out the query song itself and format results
        recommendations = []
        for result in results:
            if result["song_id"] != song_id:  # Exclude query song
                recommendations.append(
                    RecommendationResponse(
                        song_id=result["song_id"],
                        name=result["name"],
                        primary_artist=result["primary_artist"],
                        album_name=result.get("album_name"),
                        language=result.get("language"),
                        similarity_score=result.get("score", 0.0),
                        raw_data=result.get("raw_data", {})
                    )
                )
            
            if len(recommendations) >= limit:
                break
        
        return RecommendationsListResponse(
            query_song_id=song_id,
            query_song_name=query_song["name"],
            recommendations=recommendations,
            total=len(recommendations)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_recommendations: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/songs/{song_id}", tags=["Songs"])
async def get_song_details(song_id: str):
    """
    Get stored song details from database
    
    Args:
        song_id: Song ID
        
    Returns:
        Song document from database
        
    Raises:
        404: If song not found
    """
    try:
        db = get_database()
        songs_collection = db.songs
        
        song = await songs_collection.find_one({"song_id": song_id})
        
        if not song:
            raise HTTPException(
                status_code=404,
                detail="Song not found in database"
            )
        
        # Remove MongoDB's _id field
        song.pop("_id", None)
        
        return {"success": True, "data": song}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching song: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats", tags=["Statistics"])
async def get_stats():
    """
    Get database statistics
    
    Returns:
        Statistics about stored songs and embeddings
    """
    try:
        db = get_database()
        songs_collection = db.songs
        
        total_songs = await songs_collection.count_documents({})
        
        # Get language distribution
        pipeline = [
            {"$group": {"_id": "$language", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 10}
        ]
        language_dist = await songs_collection.aggregate(pipeline).to_list(length=10)
        
        return {
            "success": True,
            "data": {
                "total_songs": total_songs,
                "language_distribution": language_dist
            }
        }
        
    except Exception as e:
        logger.error(f"Error fetching stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom HTTP exception handler"""
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "error": exc.detail}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Catch-all exception handler"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
            "detail": str(exc)
        }
    )


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=True,  # Enable auto-reload during development
        log_level="info"
    )
