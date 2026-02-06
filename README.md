---
title: Saafy Music Recommender
emoji: 🎵
colorFrom: purple
colorTo: pink
sdk: gradio
sdk_version: 4.44.0
app_file: app.py
pinned: false
license: mit
---

# 🎵 Saafy Music Recommender

Intelligent music recommendation API powered by ML embeddings and vector search.

## Features

- 🔍 **Search Proxy** - Seamlessly search songs from Saafy API
- 🤖 **ML-Powered Recommendations** - Uses sentence-transformers for semantic similarity
- 🗄️ **MongoDB Vector Search** - Fast similarity lookups with Atlas Vector Search
- ⚡ **Background Processing** - Automatic song ingestion and embedding generation
- 📊 **Statistics API** - Track database metrics and language distribution

## API Endpoints

### Health Check
```
GET /
```

### Search Songs
```
GET /proxy/search?query=song_name&page=0&limit=10
```

### Get Recommendations
```
GET /recommend/{song_id}?limit=10
```

### Get Song Details
```
GET /songs/{song_id}
```

### Database Statistics
```
GET /stats
```

## Tech Stack

- **FastAPI** - Modern Python web framework
- **sentence-transformers** - ML model for embeddings (all-MiniLM-L6-v2)
- **MongoDB Atlas** - Database with Vector Search
- **Motor** - Async MongoDB driver
- **Uvicorn** - ASGI server

## How It Works

1. User searches for a song via `/proxy/search`
2. Results are returned immediately from Saafy API
3. Songs are processed in background: metadata → text → 384D embedding
4. Embeddings stored in MongoDB with vector index
5. `/recommend` endpoint uses vector similarity search to find similar songs

## Model Info

- **Model:** sentence-transformers/all-MiniLM-L6-v2
- **Embedding Dimensions:** 384
- **Similarity Metric:** Cosine similarity
- **Vector Index:** MongoDB Atlas Vector Search

## Development

Built with ❤️ for music lovers who want smart recommendations without the bloat.
