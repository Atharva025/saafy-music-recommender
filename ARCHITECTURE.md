# System Architecture Documentation

## 🏗️ Architecture Overview

The Music Recommendation Backend is a three-tier system that sits between your frontend and the Saafy API, enriching the data flow with ML-powered recommendations.

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND (React/Vue/etc)                 │
│                     http://localhost:3000                       │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            │ HTTP Requests
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                   FASTAPI BACKEND (This Service)                │
│                     http://localhost:8000                       │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    API LAYER (main.py)                   │  │
│  │  • /proxy/search - Search proxy endpoint                │  │
│  │  • /recommend/{id} - Get recommendations                │  │
│  │  • /songs/{id} - Get song details                       │  │
│  │  • /stats - Database statistics                         │  │
│  └────────┬──────────────────────────────┬──────────────────┘  │
│           │                               │                     │
│           │                               │                     │
│  ┌────────▼──────────┐         ┌─────────▼──────────┐         │
│  │   ML ENGINE       │         │   DATABASE LAYER   │         │
│  │  (ml_engine.py)   │         │   (database.py)    │         │
│  │                   │         │                    │         │
│  │  • Model: MiniLM  │         │  • Motor (async)   │         │
│  │  • 384 dimensions │         │  • PyMongo         │         │
│  │  • Embedding gen  │         │  • Connection mgmt │         │
│  └───────────────────┘         └──────────┬─────────┘         │
│                                            │                    │
└────────────────────────────────────────────┼────────────────────┘
                                             │
                 ┌───────────────────────────┼───────────────────┐
                 │                           │                   │
                 │                           ▼                   │
                 │           ┌────────────────────────┐          │
                 │           │   MONGODB ATLAS        │          │
                 │           │   (Cloud Database)     │          │
                 │           │                        │          │
                 │           │  Collection: songs     │          │
                 │           │  ┌──────────────────┐  │          │
                 │           │  │ song_id          │  │          │
                 │           │  │ name             │  │          │
                 │           │  │ primary_artist   │  │          │
                 │           │  │ album_name       │  │          │
                 │           │  │ language         │  │          │
                 │           │  │ embedding: [384] │◄─┼──────────┤
                 │           │  │ raw_data: {...}  │  │  Vector  │
                 │           │  └──────────────────┘  │  Search  │
                 │           │                        │  Index   │
                 │           └────────────────────────┘          │
                 │                                               │
                 │  External API Call                            │
                 │                                               │
                 └──────────────────┬────────────────────────────┘
                                    │
                                    ▼
                   ┌────────────────────────────────┐
                   │    SAAFY API (External)        │
                   │  https://saafy-api.vercel.app  │
                   │                                │
                   │  • /api/search/songs          │
                   │  • Song metadata              │
                   │  • No ML capabilities         │
                   └────────────────────────────────┘
```

---

## 🔄 Data Flow Diagrams

### 1. Search Flow (Lazy Loading)

```
┌──────────┐
│ Frontend │
└────┬─────┘
     │ 1. GET /proxy/search?query=Believer
     ▼
┌─────────────────────────────────────────────────┐
│              FastAPI Backend                    │
│                                                 │
│  main.py: proxy_search()                       │
│    │                                            │
│    │ 2. Fetch from Saafy API                   │
│    ├──────────────────────────────┐            │
│    │                               │            │
│    ▼                               ▼            │
│  Return Results Immediately    Background Task │
│  (Don't block user)            (Non-blocking)  │
│    │                               │            │
│    │                               │            │
└────┼───────────────────────────────┼────────────┘
     │                               │
     │                               │ 3. For each song:
     │                               │    - Check if exists
     │                               │    - Generate embedding
     │                               │    - Store in MongoDB
     │                               ▼
     │                         ┌──────────────┐
     │                         │   ML Engine  │
     │                         │  (MiniLM)    │
     │                         └──────┬───────┘
     │                                │
     │                                │ 4. Text → Vector
     │                                │    [0.1, 0.2, ..., 0.384]
     │                                ▼
     │                         ┌──────────────┐
     │                         │   MongoDB    │
     │                         │   Insert     │
     │                         └──────────────┘
     │
     │ 5. Return JSON response
     ▼
┌──────────┐
│ Frontend │
│ Shows    │
│ Results  │
└──────────┘
```

**Key Points:**
- User sees results immediately (no waiting for ML processing)
- Embeddings generated in background
- Songs are stored only once (duplicate check)
- Next search for same song is instant (already in DB)

---

### 2. Recommendation Flow (Vector Search)

```
┌──────────┐
│ Frontend │
└────┬─────┘
     │ 1. GET /recommend/song123?limit=10
     ▼
┌─────────────────────────────────────────────────┐
│              FastAPI Backend                    │
│                                                 │
│  main.py: get_recommendations()                │
│    │                                            │
│    │ 2. Query MongoDB for song123              │
│    ▼                                            │
│  ┌──────────────────────────────┐              │
│  │ songs.find_one({             │              │
│  │   song_id: "song123"         │              │
│  │ })                            │              │
│  └──────────┬───────────────────┘              │
│             │                                    │
│             │ Returns:                           │
│             │ {                                  │
│             │   embedding: [0.1, 0.2, ..., 0.9] │
│             │   name: "Believer"                 │
│             │   ...                              │
│             │ }                                  │
│             │                                    │
│             │ 3. Run Vector Search               │
│             ▼                                    │
│  ┌──────────────────────────────┐              │
│  │ Aggregation Pipeline:        │              │
│  │                              │              │
│  │ $vectorSearch {              │              │
│  │   index: "vector_index"      │              │
│  │   queryVector: [0.1, ...]    │              │
│  │   limit: 10                  │              │
│  │   similarity: "cosine"       │              │
│  │ }                            │              │
│  └──────────┬───────────────────┘              │
│             │                                    │
└─────────────┼────────────────────────────────────┘
              │
              │ 4. MongoDB Atlas computes
              │    cosine similarity across
              │    all embeddings
              ▼
        ┌──────────────────┐
        │  MongoDB Atlas   │
        │  Vector Search   │
        │                  │
        │  Compare:        │
        │  Query: [0.1...] │
        │  vs              │
        │  All DB vectors  │
        │                  │
        │  Find top 10     │
        │  most similar    │
        └────────┬─────────┘
                 │
                 │ 5. Returns ranked results
                 │    with similarity scores
                 ▼
        ┌────────────────────────────┐
        │ [                          │
        │   {song: "Thunder",        │
        │    score: 0.92},           │
        │   {song: "Radioactive",    │
        │    score: 0.89},           │
        │   ...                      │
        │ ]                          │
        └────────┬───────────────────┘
                 │
                 │ 6. Format response
                 ▼
        ┌───────────────────┐
        │  Frontend          │
        │  Display           │
        │  Recommendations   │
        └────────────────────┘
```

**Key Points:**
- Requires song to be in database first
- Uses MongoDB Atlas Vector Search (not manual comparison)
- Cosine similarity: measures angle between vectors
- Scores close to 1.0 = very similar songs
- Results are deterministic and consistent

---

## 🧮 How Embeddings Work

### Text Representation

Each song is converted to a semantic text string:

```python
text = f"{song_name} {artist} {album} {language}"

# Example:
"Believer Imagine Dragons Evolve english"
```

### Embedding Generation

```
Original Text:
"Believer Imagine Dragons Evolve english"
         │
         │ SentenceTransformer (all-MiniLM-L6-v2)
         ▼
384-Dimensional Vector:
[
  0.0234,  0.1567, -0.0891,  0.2341,  0.0123, ...
  # 384 floating point numbers
]
```

**Why 384 dimensions?**
- Each dimension captures different semantic features
- Collectively encodes: genre, mood, tempo, style, artist similarity
- More dimensions = more nuanced understanding

### Similarity Calculation (Cosine Similarity)

```
Song A: [0.2, 0.5, 0.1, ...]
Song B: [0.3, 0.4, 0.2, ...]

Cosine Similarity = (A · B) / (||A|| × ||B||)

Result: 0.0 to 1.0
- 1.0 = identical songs
- 0.9+ = very similar
- 0.7+ = somewhat similar
- <0.5 = different
```

**Visual Representation:**

```
       Song A
         ↑
         │ ⟋ Small angle = High similarity
         │⟋
    ─────┴─────→ Song B

       Song C
         ↑
         │
         │     Large angle = Low similarity
         │
    ─────┴─────→ Song D
```

---

## 💾 Database Schema

### MongoDB Collection: `songs`

```javascript
{
  "_id": ObjectId("..."),              // MongoDB auto-generated
  
  "song_id": "abc123",                 // Unique ID from Saafy API
  "name": "Believer",                  // Song name
  "primary_artist": "Imagine Dragons", // Main artist
  "album_name": "Evolve",              // Album
  "language": "english",               // Language
  
  "embedding": [                       // 384-dimensional vector
    0.0234, 0.1567, -0.0891, ...      // (384 numbers total)
  ],
  
  "raw_data": {                        // Complete Saafy API response
    "id": "abc123",
    "name": "Believer",
    "artists": {
      "primary": [...],
      "featured": [...]
    },
    "image": [...],
    "downloadUrl": [...],
    // ... all original fields
  }
}
```

**Indexes:**

1. **Regular Index** (Python creates automatically)
   - `song_id` - Unique index for fast lookups
   - `language` - Filter by language

2. **Vector Search Index** (Manual creation in Atlas UI)
   ```json
   {
     "fields": [
       {
         "type": "vector",
         "path": "embedding",
         "numDimensions": 384,
         "similarity": "cosine"
       }
     ]
   }
   ```

---

## 🧩 Component Breakdown

### main.py (API Layer)
- FastAPI application setup
- Route definitions
- Request/response handling
- Background task coordination
- Error handling

**Key Functions:**
- `proxy_search()` - Proxy to Saafy API + background ingestion
- `get_recommendations()` - Vector search aggregation
- `process_and_store_song()` - Background embedding generation

### ml_engine.py (ML Layer)
- Sentence transformer model management
- Embedding generation
- Text preprocessing

**Key Functions:**
- `generate_embedding(text)` - Text → 384D vector
- `create_song_text()` - Format song data for embedding

### database.py (Data Layer)
- MongoDB connection management
- Index creation
- Database operations

**Key Functions:**
- `connect_to_mongo()` - Establish connection
- `get_database()` - Get DB instance
- `create_indexes()` - Setup indexes

### schemas.py (Type Safety)
- Pydantic models for validation
- Request/response structure
- Type hints

**Key Models:**
- `SongResponse` - Saafy API response
- `SongDocument` - MongoDB document
- `RecommendationResponse` - Recommendation result

### config.py (Configuration)
- Environment variable management
- Settings validation
- Configuration access

---

## ⚡ Performance Characteristics

| Operation | Time | Notes |
|-----------|------|-------|
| Search proxy | ~200ms | Dominated by Saafy API call |
| Embedding generation | 50-100ms | Per song, runs in background |
| Database insert | 10-20ms | Async, non-blocking |
| Vector search | 50-100ms | For 10k songs, scales logarithmically |
| Startup time | 2-3s | Model loading (first time: +10s for download) |

**Scalability:**
- MongoDB Atlas Vector Search is optimized for millions of vectors
- Background processing prevents blocking user requests
- Async/await enables high concurrency
- Stateless design allows horizontal scaling

---

## 🔒 Security Considerations

### Current (Development)
```python
allow_origins=["*"]  # Allow all domains
```

### Production
```python
allow_origins=[
    "https://yourdomain.com",
    "https://app.yourdomain.com"
]
```

**Additional Security:**
1. **API Keys:** Add authentication headers
2. **Rate Limiting:** Prevent abuse
3. **HTTPS Only:** SSL/TLS encryption
4. **MongoDB Auth:** Use strong passwords
5. **IP Whitelisting:** Restrict MongoDB access
6. **Environment Secrets:** Never commit `.env`

---

## 🚀 Scaling Strategies

### Vertical Scaling
- Increase server RAM for more concurrent requests
- More CPU cores for parallel processing

### Horizontal Scaling
```
Load Balancer
     │
     ├──→ Backend Instance 1
     ├──→ Backend Instance 2
     ├──→ Backend Instance 3
     │
     └──→ Shared MongoDB Atlas
```

### Caching Layer
```
Request → Redis Cache → Backend → MongoDB
          (Fast)        (Smart)   (Storage)
```

### Queue-Based Processing
```
Search → Response → Queue (RabbitMQ) → Worker Pool → MongoDB
         (Instant)   (Buffer)          (Process)     (Store)
```

---

## 📊 Monitoring & Observability

**Logging Points:**
- API request/response times
- Background task completion
- Database connection status
- Embedding generation time
- Vector search performance

**Metrics to Track:**
- Requests per second
- Average embedding time
- Database query latency
- Vector search accuracy
- Cache hit rate (if implemented)

**Tools:**
- Application: Python `logging` module
- Infrastructure: Prometheus + Grafana
- MongoDB: Atlas monitoring dashboard
- API: FastAPI built-in `/metrics` endpoint

---

## 🧪 Testing Strategy

1. **Unit Tests:** Test individual functions
2. **Integration Tests:** Test API endpoints
3. **Load Tests:** Simulate concurrent users
4. **Accuracy Tests:** Validate recommendation quality

**Run the test suite:**
```bash
python test_setup.py
```

---

This architecture enables:
- ✅ Fast user responses (no blocking)
- ✅ Intelligent recommendations (ML-powered)
- ✅ Scalable design (async + cloud DB)
- ✅ Production-ready (error handling, logging)
- ✅ Easy maintenance (modular, type-safe)
