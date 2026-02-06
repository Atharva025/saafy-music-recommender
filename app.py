"""
Gradio Interface + REST API for Saafy Music Recommender
Combines Gradio web UI with FastAPI REST endpoints
"""
import gradio as gr
import asyncio
import json
from typing import Optional, List
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

# Import backend functions
from config import get_settings
from database import connect_to_mongo, close_mongo_connection, get_database, check_vector_index_exists
from ml_engine import initialize_ml_engine, get_ml_engine
from main import fetch_from_saafy, process_and_store_song, ingest_songs_background
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="Saafy Music Recommender API")

# Global initialization flag
_initialized = False

async def initialize_app():
    """Initialize ML engine and MongoDB connection"""
    global _initialized
    if _initialized:
        return  # Already initialized
        
    logger.info("Initializing application...")
    
    try:
        settings = get_settings()
        logger.info(f"Settings loaded: DB={settings.mongodb_db_name}")
        
        # Initialize ML Engine
        initialize_ml_engine(settings.model_name)
        logger.info("ML Engine initialized")
        
        # Connect to MongoDB
        await connect_to_mongo()
        logger.info("Database connected")
        
        # Check vector index
        await check_vector_index_exists()
        
        _initialized = True
        logger.info("Application ready!")
    except Exception as e:
        error_msg = str(e)
        if "Field required" in error_msg or "validation error" in error_msg:
            logger.error("❌ Environment variables not set! Check HF Spaces secrets.")
            raise Exception("⚠️ Configuration error: Environment variables (MONGODB_URI, MONGODB_DB_NAME, SAAFY_API_BASE_URL) are not set in HF Spaces secrets!")
        logger.error(f"Initialization failed: {e}", exc_info=True)
        raise

async def search_songs(query: str, limit: int = 10):
    """Search for songs from Saafy API"""
    try:
        # Lazy initialization on first request
        await initialize_app()
        
        if not query.strip():
            return "⚠️ Please enter a search query"
        
        # Fetch from Saafy API
        params = {"query": query, "page": 0, "limit": limit}
        data = fetch_from_saafy("/search/songs", params)
        
        if not data.get("success"):
            return f"❌ Search failed: {data.get('message', 'Unknown error')}"
        
        results = data.get("data", {}).get("results", [])
        
        if not results:
            return f"🔍 No results found for '{query}'"
        
        # Trigger background ingestion (fire and forget)
        asyncio.create_task(ingest_songs_background(results))
        
        # Format results
        output = f"🎵 Found {len(results)} songs for '{query}':\n\n"
        for i, song in enumerate(results, 1):
            name = song.get("name", "Unknown")
            artists = song.get("artists", {}).get("primary", [])
            artist_name = artists[0].get("name") if artists else "Unknown Artist"
            album = song.get("album", {}).get("name", "")
            song_id = song.get("id", "")
            
            output += f"{i}. **{name}** by {artist_name}\n"
            if album:
                output += f"   Album: {album}\n"
            output += f"   ID: `{song_id}`\n\n"
        
        output += "✅ Songs queued for ML processing in background!"
        return output
        
    except Exception as e:
        logger.error(f"Search error: {e}", exc_info=True)
        return f"❌ Error: {str(e)}"


async def get_recommendations_async(song_id: str, limit: int = 10):
    """Get recommendations for a song"""
    try:
        if not song_id.strip():
            return "⚠️ Please enter a song ID"
        
        await initialize_app()
        
        db = get_database()
        songs_collection = db.songs
        
        # Find the query song
        query_song = await songs_collection.find_one({"song_id": song_id})
        
        if not query_song:
            return f"❌ Song ID '{song_id}' not found in database.\n\n💡 Search for it first to process it!"
        
        # Get embedding
        query_embedding = query_song.get("embedding")
        if not query_embedding:
            return "❌ Song embedding not found"
        
        # Vector search
        pipeline = [
            {
                "$vectorSearch": {
                    "index": "vector_index",
                    "path": "embedding",
                    "queryVector": query_embedding,
                    "numCandidates": limit * 10,
                    "limit": limit + 1,
                }
            },
            {
                "$project": {
                    "song_id": 1,
                    "name": 1,
                    "primary_artist": 1,
                    "album_name": 1,
                    "language": 1,
                    "score": {"$meta": "vectorSearchScore"}
                }
            }
        ]
        
        cursor = songs_collection.aggregate(pipeline)
        results = await cursor.to_list(length=limit + 1)
        
        # Filter out query song
        recommendations = [r for r in results if r["song_id"] != song_id][:limit]
        
        if not recommendations:
            return f"❌ No recommendations found for '{query_song['name']}'"
        
        # Format output
        output = f"🎵 Recommendations for **{query_song['name']}** by {query_song.get('primary_artist', 'Unknown')}:\n\n"
        
        for i, rec in enumerate(recommendations, 1):
            name = rec.get("name", "Unknown")
            artist = rec.get("primary_artist", "Unknown")
            score = rec.get("score", 0)
            similarity = int(score * 100)
            
            output += f"{i}. **{name}** by {artist}\n"
            output += f"   Similarity: {similarity}%\n"
            output += f"   ID: `{rec['song_id']}`\n\n"
        
        return output
        
    except Exception as e:
        logger.error(f"Recommendation error: {e}", exc_info=True)
        return f"❌ Error: {str(e)}"


# Gradio 4.44+ supports async functions directly - no wrapper needed!


async def get_stats_async():
    """Get database statistics"""
    try:
        await initialize_app()
        
        db = get_database()
        songs_collection = db.songs
        
        total_songs = await songs_collection.count_documents({})
        
        # Language distribution
        pipeline = [
            {"$group": {"_id": "$language", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 10}
        ]
        language_dist = await songs_collection.aggregate(pipeline).to_list(length=10)
        
        output = f"📊 **Database Statistics**\n\n"
        output += f"🎵 Total songs processed: **{total_songs}**\n\n"
        
        if language_dist:
            output += "**Top Languages:**\n"
            for item in language_dist:
                lang = item["_id"] or "Unknown"
                count = item["count"]
                output += f"- {lang}: {count} songs\n"

    
    except Exception as e:
        logger.error(f"Stats error: {e}", exc_info=True)
        return f"❌ Error: {str(e)}"
    
    return output
        
# ============================================
# REST API Endpoints (FastAPI)
# ============================================

@app.on_event("startup")
async def startup_event():
    """Initialize on FastAPI startup"""
    await initialize_app()

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    await close_mongo_connection()

@app.get("/")
async def root():
    """Redirect to Gradio UI"""
    return {"message": "Use /api/* for REST endpoints or visit the Gradio UI"}

@app.get("/api/recommend/{song_id}")
async def api_recommend(song_id: str, limit: int = 10):
    """
    REST API: Get recommendations for a song
    
    Example: GET /api/recommend/Starboy!?limit=10
    """
    try:
        await initialize_app()
        
        db = get_database()
        songs_collection = db.songs
        
        # Find the query song
        query_song = await songs_collection.find_one({"song_id": song_id})
        
        if not query_song:
            raise HTTPException(status_code=404, detail=f"Song ID '{song_id}' not found in database")
        
        # Get embedding
        query_embedding = query_song.get("embedding")
        if not query_embedding:
            raise HTTPException(status_code=400, detail="Song embedding not found")
        
        # Vector search
        pipeline = [
            {
                "$vectorSearch": {
                    "index": "vector_index",
                    "path": "embedding",
                    "queryVector": query_embedding,
                    "numCandidates": limit * 10,
                    "limit": limit + 1,
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "song_id": 1,
                    "name": 1,
                    "primary_artist": 1,
                    "album_name": 1,
                    "language": 1,
                    "score": {"$meta": "vectorSearchScore"}
                }
            }
        ]
        
        cursor = songs_collection.aggregate(pipeline)
        results = await cursor.to_list(length=limit + 1)
        
        # Filter out query song
        recommendations = [r for r in results if r["song_id"] != song_id][:limit]
        
        return {
            "success": True,
            "query_song": {
                "song_id": query_song["song_id"],
                "name": query_song["name"],
                "primary_artist": query_song.get("primary_artist", "Unknown")
            },
            "recommendations": recommendations,
            "count": len(recommendations)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Recommendation error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/search")
async def api_search(query: str, limit: int = 10):
    """
    REST API: Search for songs
    
    Example: GET /api/search?query=starboy&limit=10
    """
    try:
        await initialize_app()
        
        if not query.strip():
            raise HTTPException(status_code=400, detail="Query parameter required")
        
        # Fetch from Saafy API
        params = {"query": query, "page": 0, "limit": limit}
        data = fetch_from_saafy("/search/songs", params)
        
        if not data.get("success"):
            raise HTTPException(status_code=500, detail=data.get('message', 'Search failed'))
        
        results = data.get("data", {}).get("results", [])
        
        # Trigger background ingestion
        asyncio.create_task(ingest_songs_background(results))
        
        return {
            "success": True,
            "query": query,
            "results": results,
            "count": len(results),
            "message": "Songs queued for processing"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Search error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/add-song")
async def api_add_song_by_name(song_name: str, artist: str = None):
    """
    REST API: Search for a song by name and add it to database immediately
    
    Example: POST /api/add-song?song_name=starboy&artist=weeknd
    """
    try:
        await initialize_app()
        
        # Search for the song
        search_query = f"{song_name} {artist}" if artist else song_name
        params = {"query": search_query, "page": 0, "limit": 5}
        data = fetch_from_saafy("/search/songs", params)
        
        if not data.get("success"):
            raise HTTPException(status_code=500, detail=data.get('message', 'Search failed'))
        
        results = data.get("data", {}).get("results", [])
        
        if not results:
            raise HTTPException(status_code=404, detail=f"No songs found for '{search_query}'")
        
        # Take the first/best match
        song = results[0]
        
        # Process and store with embedding immediately
        await process_and_store_song(song)
        
        # Get artist name
        artists = song.get("artists", {}).get("primary", [])
        artist_name = artists[0].get("name") if artists else "Unknown Artist"
        
        return {
            "success": True,
            "message": f"Song added to database successfully",
            "song_id": song.get("id"),
            "name": song.get("name"),
            "primary_artist": artist_name,
            "album": song.get("album", {}).get("name"),
            "language": song.get("language")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Add song error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/process/{song_id}")
async def api_process_song(song_id: str):
    """
    REST API: Process and add a specific song to database by song ID
    
    Example: POST /api/process/fW-Mxsnu
    """
    try:
        await initialize_app()
        
        # Fetch song details from Saafy API
        data = fetch_from_saafy(f"/songs/{song_id}", {})
        
        if not data.get("success"):
            raise HTTPException(status_code=404, detail=f"Song not found in Saafy API: {song_id}")
        
        song_data = data.get("data", {}).get("song", [])
        if not song_data:
            raise HTTPException(status_code=404, detail="No song data returned")
        
        song = song_data[0] if isinstance(song_data, list) else song_data
        
        # Process and store with embedding
        await process_and_store_song(song)
        
        return {
            "success": True,
            "message": f"Song '{song.get('name', song_id)}' processed and added to database",
            "song_id": song_id,
            "name": song.get("name"),
            "primary_artist": song.get("primary_artists", song.get("artists", {})).get("primary", [{}])[0].get("name") if song.get("primary_artists") or song.get("artists") else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Process song error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stats")
async def api_stats():
    """
    REST API: Get database statistics
    
    Example: GET /api/stats
    """
    try:
        await initialize_app()
        
        db = get_database()
        songs_collection = db.songs
        
        total_songs = await songs_collection.count_documents({})
        
        # Language distribution
        pipeline = [
            {"$group": {"_id": "$language", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 10}
        ]
        language_dist = await songs_collection.aggregate(pipeline).to_list(length=10)
        
        return {
            "success": True,
            "total_songs": total_songs,
            "languages": [{"language": item["_id"] or "Unknown", "count": item["count"]} for item in language_dist]
        }
        
    except Exception as e:
        logger.error(f"Stats error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# ============================================
# Gradio UI Components
# ============================================

# Gradio 4.44+ supports async functions directly - no wrapper needed!



# Create Gradio interface
with gr.Blocks(title="🎵 Saafy Music Recommender", theme=gr.themes.Soft()) as demo:
    gr.Markdown("""
    # 🎵 Saafy Music Recommender
    ### Intelligent music recommendations powered by ML embeddings
    
    **How it works:**
    1. **Search** for songs to add them to the database
    2. **Get Recommendations** based on similarity using ML embeddings
    3. View **Statistics** about the database
    """)
    
    with gr.Tabs():
        # Search Tab
        with gr.Tab("🔍 Search Songs"):
            gr.Markdown("Search for songs from Saafy API. Found songs will be processed and added to the database.")
            with gr.Row():
                search_query = gr.Textbox(label="Search Query", placeholder="Enter song name, artist, or album...")
                search_limit = gr.Slider(minimum=1, maximum=50, value=10, step=1, label="Number of Results")
            search_button = gr.Button("Search", variant="primary")
            search_output = gr.Markdown(label="Results")
            
            search_button.click(
                fn=search_songs,
                inputs=[search_query, search_limit],
                outputs=search_output
            )
        
        # Recommendations Tab
        with gr.Tab("🎯 Get Recommendations"):
            gr.Markdown("Get AI-powered recommendations based on a song. The song must be in the database first (search for it!).")
            with gr.Row():
                rec_song_id = gr.Textbox(label="Song ID", placeholder="Enter song ID from search results...")
                rec_limit = gr.Slider(minimum=1, maximum=50, value=10, step=1, label="Number of Recommendations")
            rec_button = gr.Button("Get Recommendations", variant="primary")
            rec_output = gr.Markdown(label="Recommendations")
            
            rec_button.click(
                fn=get_recommendations_async,
                inputs=[rec_song_id, rec_limit],
                outputs=rec_output
            )
        
        # Statistics Tab
        with gr.Tab("📊 Database Stats"):
            gr.Markdown("View statistics about the processed songs database.")
            stats_button = gr.Button("Refresh Statistics", variant="primary")
            stats_output = gr.Markdown(label="Statistics")
            
            stats_button.click(
                fn=get_stats_async,
                inputs=[],
                outputs=stats_output
            )
    
    gr.Markdown("""
    ---
    **Note:** First request may take 3-5 seconds while ML model loads. Background song processing happens automatically after search.
    
    **REST API Available:**
    - `POST /api/add-song?song_name=starboy&artist=weeknd` - Add song by name (instant)
    - `GET /api/search?query=starboy&limit=10` - Search multiple songs (background processing)
    - `GET /api/recommend/{song_id}?limit=10` - Get recommendations
    - `POST /api/process/{song_id}` - Process specific song by ID
    - `GET /api/stats` - Database statistics
    """)

# Mount Gradio on FastAPI
app = gr.mount_gradio_app(app, demo, path="/")

# Launch
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)
