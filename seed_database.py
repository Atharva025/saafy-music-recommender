"""
Database Seeding Script
Pre-loads popular songs into MongoDB with embeddings for instant recommendations
"""
import asyncio
import sys
from typing import List, Dict
import requests
import tqdm as tqdm_module

# Import from our modules
from config import get_settings
from database import connect_to_mongo, close_mongo_connection, get_database
from ml_engine import initialize_ml_engine, get_ml_engine
from schemas import SongDocument


# Popular search queries to seed the database
SEED_QUERIES = [
    "Imagine Dragons",
    "Ed Sheeran",
    "The Weeknd",
    "Taylor Swift",
    "Ariana Grande",
    "Billie Eilish",
    "Post Malone",
    "Drake",
    "Justin Bieber",
    "Dua Lipa",
    "Coldplay",
    "Maroon 5",
    "Bruno Mars",
    "Sia",
    "Eminem",
    "Adele",
    "Sam Smith",
    "Shawn Mendes",
    "Charlie Puth",
    "OneRepublic",
]


def fetch_songs_from_saafy(query: str, limit: int = 10) -> List[Dict]:
    """
    Fetch songs from Saafy API
    
    Args:
        query: Search query
        limit: Number of results
        
    Returns:
        List of song dictionaries
    """
    settings = get_settings()
    url = f"{settings.saafy_api_base_url}/search/songs"
    params = {"query": query, "limit": limit, "page": 0}
    
    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        if data.get("success") and data.get("data"):
            return data["data"].get("results", [])
        return []
    except Exception as e:
        print(f"  ⚠️  Error fetching '{query}': {e}")
        return []


async def process_song(song_data: Dict, db) -> bool:
    """
    Process a single song: generate embedding and store
    
    Args:
        song_data: Raw song data from Saafy API
        db: Database instance
        
    Returns:
        True if successful, False otherwise
    """
    try:
        song_id = song_data.get("id")
        if not song_id:
            return False
        
        songs_collection = db.songs
        
        # Check if already exists
        existing = await songs_collection.find_one({"song_id": song_id})
        if existing:
            return False  # Already in DB, skip
        
        # Extract fields
        name = song_data.get("name", "Unknown")
        language = song_data.get("language", "")
        
        artists = song_data.get("artists", {})
        primary_artists = artists.get("primary", [])
        primary_artist = primary_artists[0].get("name") if primary_artists else "Unknown"
        
        album = song_data.get("album", {})
        album_name = album.get("name", "") if album else ""
        
        # Generate embedding
        ml_engine = get_ml_engine()
        song_text = ml_engine.create_song_text(
            name=name,
            artist=primary_artist,
            album=album_name,
            language=language
        )
        embedding = ml_engine.generate_embedding(song_text)
        
        # Create and insert document
        song_doc = SongDocument(
            song_id=song_id,
            name=name,
            language=language,
            primary_artist=primary_artist,
            album_name=album_name,
            embedding=embedding,
            raw_data=song_data
        )
        
        await songs_collection.insert_one(song_doc.model_dump())
        return True
        
    except Exception as e:
        # Silently handle errors to not spam console
        return False


async def seed_database(queries: List[str], songs_per_query: int = 10):
    """
    Seed database with popular songs
    
    Args:
        queries: List of search queries
        songs_per_query: Number of songs to fetch per query
    """
    print("\n" + "=" * 70)
    print("🎵 DATABASE SEEDING SCRIPT")
    print("=" * 70)
    print(f"\nThis will pre-load ~{len(queries) * songs_per_query} popular songs")
    print("into your MongoDB database with ML embeddings.\n")
    
    # Initialize
    print("📦 Initializing...")
    settings = get_settings()
    initialize_ml_engine(settings.model_name)
    await connect_to_mongo()
    db = get_database()
    
    print("✓ ML model loaded")
    print("✓ Database connected\n")
    
    # Fetch all songs first
    print(f"🔍 Fetching songs from Saafy API ({len(queries)} queries)...")
    all_songs = []
    
    for query in tqdm_module.tqdm(queries, desc="Fetching", ncols=70):
        songs = fetch_songs_from_saafy(query, songs_per_query)
        all_songs.extend(songs)
        await asyncio.sleep(0.5)  # Rate limiting
    
    print(f"\n✓ Fetched {len(all_songs)} songs total\n")
    
    # Process and store songs
    print("🤖 Generating embeddings and storing in MongoDB...")
    print("   (This may take 2-3 minutes)\n")
    
    new_songs = 0
    skipped = 0
    
    # Process with progress bar
    for song in tqdm_module.tqdm(all_songs, desc="Processing", ncols=70):
        success = await process_song(song, db)
        if success:
            new_songs += 1
        else:
            skipped += 1
        
        # Small delay to not overwhelm
        await asyncio.sleep(0.1)
    
    # Summary
    print("\n" + "=" * 70)
    print("✅ SEEDING COMPLETE!")
    print("=" * 70)
    print(f"\n📊 Summary:")
    print(f"   • New songs added:     {new_songs}")
    print(f"   • Already existed:     {skipped}")
    print(f"   • Total in database:   {new_songs + skipped}")
    
    # Show some sample songs
    print(f"\n🎵 Sample songs in database:")
    songs_collection = db.songs
    sample = await songs_collection.find().limit(5).to_list(length=5)
    
    for i, song in enumerate(sample, 1):
        print(f"   {i}. {song['name']} - {song['primary_artist']}")
    
    print("\n" + "=" * 70)
    print("🚀 READY TO USE!")
    print("=" * 70)
    print("\nYou can now:")
    print("  1. Start the server: python main.py")
    print("  2. Get recommendations for any seeded song")
    print("  3. Search for more songs to expand the database")
    print("\nExample:")
    print('  curl "http://localhost:8000/recommend/SONG_ID?limit=10"')
    print("\n" + "=" * 70 + "\n")
    
    # Cleanup
    await close_mongo_connection()


async def check_existing_data():
    """Check if database already has data"""
    try:
        await connect_to_mongo()
        db = get_database()
        count = await db.songs.count_documents({})
        await close_mongo_connection()
        return count
    except:
        return 0


async def main():
    """Main entry point"""
    try:
        # Check existing data
        existing_count = await check_existing_data()
        
        if existing_count > 0:
            print(f"\n⚠️  Database already has {existing_count} songs.")
            response = input("Continue adding more songs? (y/n): ").strip().lower()
            if response != 'y':
                print("Seeding cancelled.")
                return
        
        # Run seeding
        await seed_database(SEED_QUERIES, songs_per_query=10)
        
    except KeyboardInterrupt:
        print("\n\n❌ Seeding interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error during seeding: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    # Check if dependencies are available
    try:
        import tqdm as tqdm_module
    except ImportError:
        print("\n❌ Missing required package: tqdm")
        print("Install it with: pip install tqdm")
        sys.exit(1)
    
    # Run the seeding process
    asyncio.run(main())
