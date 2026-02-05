# Music Recommendation Backend

A production-ready FastAPI backend service that acts as an intelligent proxy between your music streaming frontend and the Saafy API. It generates ML-powered song recommendations using vector embeddings.

## 🎯 Features

- **Lazy Loading Architecture**: Songs are embedded and stored only when searched/accessed
- **Vector Similarity Search**: Uses MongoDB Atlas Vector Search with cosine similarity
- **Async/Await**: Fully asynchronous for high performance
- **Background Processing**: Non-blocking embedding generation
- **Production Ready**: Comprehensive error handling, logging, and type safety

## 🛠️ Tech Stack

- **Python 3.10+**
- **FastAPI** - Modern async web framework
- **MongoDB Atlas** - Vector database with Atlas Vector Search
- **Sentence Transformers** - ML model for embeddings (all-MiniLM-L6-v2, 384 dimensions)
- **Motor** - Async MongoDB driver

## 📁 Project Structure

```
music-rec-backend/
├── main.py            # FastAPI app, routes, and business logic
├── config.py          # Settings and environment management
├── database.py        # MongoDB connection and index configuration
├── ml_engine.py       # ML model and embedding generation
├── schemas.py         # Pydantic models for validation
├── requirements.txt   # Python dependencies
├── .env              # Environment variables (create from template)
└── README.md         # This file
```

## 🚀 Setup Instructions

### 1. Install Dependencies

```bash
cd music-rec-backend
pip install -r requirements.txt
```

On first run, `sentence-transformers` will download the model (~80MB).

### 2. Configure Environment Variables

Copy the `.env` file and fill in your MongoDB credentials:

```env
MONGODB_URI=mongodb+srv://<username>:<password>@<cluster>.mongodb.net/?retryWrites=true&w=majority
MONGODB_DB_NAME=music_recommendations
SAAFY_API_BASE_URL=https://saafy-api.vercel.app/api
HOST=0.0.0.0
PORT=8000
```

**To get your MongoDB URI:**
1. Go to [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
2. Create a free cluster (M0 tier is sufficient)
3. Click "Connect" → "Drivers" → Copy connection string
4. Replace `<username>` and `<password>` with your credentials

### 3. Create MongoDB Atlas Vector Search Index

**⚠️ CRITICAL STEP - Without this, recommendations will not work!**

1. **Go to your MongoDB Atlas Dashboard**
2. **Navigate to:** Your Cluster → "Search" tab (in left sidebar)
3. **Click:** "Create Search Index"
4. **Choose:** "JSON Editor"
5. **Paste this configuration:**

```json
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
```

6. **Set these values:**
   - **Index Name:** `vector_index` (must match exactly!)
   - **Database:** `music_recommendations` (or your DB name from .env)
   - **Collection:** `songs`

7. **Click:** "Create Search Index"
8. **Wait:** 1-2 minutes for the index to become "Active"

### 4. Run the Server

```bash
python main.py
```

Or using uvicorn directly:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The server will start at `http://localhost:8000`

### 5. Verify Installation

Open your browser and visit:
- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/

## 📡 API Endpoints

### 1. **Search Proxy** - `/proxy/search`

Acts as a proxy to Saafy API while background-processing and storing songs.

**Request:**
```http
GET /proxy/search?query=Imagine%20Dragons&page=0&limit=10
```

**Response:**
```json
{
  "success": true,
  "data": {
    "total": 100,
    "start": 1,
    "results": [...]
  }
}
```

**What happens behind the scenes:**
1. Fetches results from Saafy API
2. Returns data immediately to frontend
3. Generates embeddings in the background for each song
4. Stores songs in MongoDB (if not already stored)

### 2. **Get Recommendations** - `/recommend/{song_id}`

Returns songs similar to the queried song using vector search.

**Request:**
```http
GET /recommend/abc123?limit=10
```

**Response:**
```json
{
  "query_song_id": "abc123",
  "query_song_name": "Believer",
  "recommendations": [
    {
      "song_id": "xyz789",
      "name": "Thunder",
      "primary_artist": "Imagine Dragons",
      "album_name": "Evolve",
      "language": "english",
      "similarity_score": 0.92,
      "raw_data": {...}
    }
  ],
  "total": 10
}
```

**Requirements:**
- Song must be in database (searched previously)
- Vector index must be active

### 3. **Get Song Details** - `/songs/{song_id}`

Retrieve stored song information from database.

**Request:**
```http
GET /songs/abc123
```

### 4. **Database Statistics** - `/stats`

Get insights about stored songs.

**Request:**
```http
GET /stats
```

## 🏗️ Architecture Flow

```
┌─────────────┐
│  Frontend   │
└──────┬──────┘
       │ 1. Search "Imagine Dragons"
       ▼
┌─────────────────────────────────────┐
│  Backend (This Service)             │
│  ┌─────────────────────────────┐   │
│  │ /proxy/search endpoint      │   │
│  └────────┬────────────────────┘   │
│           │                          │
│  2. Fetch│from Saafy API            │
│           ▼                          │
│  ┌──────────────────┐               │
│  │  Return Results  │─────┐         │
│  │  Immediately     │     │         │
│  └──────────────────┘     │         │
│                            │         │
│  ┌─────────────────────────┘        │
│  │ 3. Background Processing         │
│  ▼                                   │
│  ┌────────────────────────────┐    │
│  │ Generate Embeddings        │    │
│  │ (sentence-transformers)    │    │
│  └────────────┬───────────────┘    │
│               │                     │
│               ▼                     │
│  ┌────────────────────────────┐   │
│  │ Store in MongoDB           │   │
│  └────────────────────────────┘   │
└─────────────────────────────────────┘
       │
       ▼
┌─────────────────┐
│  MongoDB Atlas  │
│  songs: {       │
│    song_id      │
│    name         │
│    embedding:   │
│     [384 dims]  │
│  }              │
└─────────────────┘
       │
       │ 4. Vector Search
       ▼
┌─────────────────────┐
│ /recommend endpoint │
│ Returns similar     │
│ songs using cosine  │
│ similarity          │
└─────────────────────┘
```

## 🔍 How Recommendations Work

1. **Text Representation**: Each song is converted to text:
   ```
   "Song Name Artist Album Language"
   Example: "Believer Imagine Dragons Evolve english"
   ```

2. **Embedding Generation**: The text is encoded into a 384-dimensional vector using `all-MiniLM-L6-v2`

3. **Vector Storage**: Embeddings are stored in MongoDB alongside song metadata

4. **Similarity Search**: When recommendations are requested:
   - Query song's embedding is retrieved
   - MongoDB Atlas Vector Search finds nearest neighbors using cosine similarity
   - Top 10 most similar songs are returned

## 🐛 Troubleshooting

### Issue: "Vector search failed"

**Solution:** Verify the vector index is created in MongoDB Atlas and is "Active"

### Issue: "Song not analyzed yet"

**Solution:** Search for the song first using `/proxy/search` to generate its embedding

### Issue: "ML model downloading on first run"

**Expected:** First run downloads the ~80MB model. Subsequent runs are instant.

### Issue: Connection timeout to MongoDB

**Solutions:**
- Verify MongoDB URI in `.env`
- Check if your IP is whitelisted in Atlas Network Access
- Ensure MongoDB cluster is running

## 🔒 Security Notes

**For Production:**
1. Change `allow_origins=["*"]` to your frontend's actual domain
2. Use environment variables for all secrets (never commit `.env`)
3. Enable MongoDB authentication and use strong passwords
4. Consider rate limiting on search endpoints
5. Add API key authentication if needed

## 📊 Performance Considerations

- **Embedding Generation**: ~50-100ms per song
- **Vector Search**: <100ms for 10k songs
- **Background Processing**: Non-blocking, doesn't slow responses
- **Scaling**: MongoDB Atlas can handle millions of vectors

## 🧪 Testing the API

Using cURL:

```bash
# Search for songs
curl "http://localhost:8000/proxy/search?query=Believer&limit=5"

# Get recommendations (replace with actual song_id from search)
curl "http://localhost:8000/recommend/<song_id>?limit=10"

# Check stats
curl "http://localhost:8000/stats"
```

Using the built-in Swagger UI:
- Navigate to http://localhost:8000/docs
- Try out endpoints interactively

## 📝 Frontend Integration

Update your frontend to call this backend instead of Saafy API directly:

**Before:**
```javascript
fetch('https://saafy-api.vercel.app/api/search/songs?query=test')
```

**After:**
```javascript
fetch('http://localhost:8000/proxy/search?query=test')
```

To get recommendations:
```javascript
// After searching, get song_id from results
fetch(`http://localhost:8000/recommend/${songId}?limit=10`)
```

## 🚦 Development vs Production

**Development:**
```bash
python main.py  # Auto-reload enabled
```

**Production:**
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

## 📈 Future Enhancements

- [ ] User-specific recommendations (collaborative filtering)
- [ ] Caching layer (Redis) for faster responses
- [ ] Batch embedding generation for efficiency
- [ ] Playlist generation based on mood/genre
- [ ] A/B testing different embedding models
- [ ] Async background workers (Celery)

## 📄 License

This project is for educational purposes. Respect Saafy API's terms of service.

## 🤝 Contributing

This is a complete, production-ready implementation. Feel free to extend with additional features!

---

**Built with ❤️ using FastAPI, MongoDB Atlas, and Sentence Transformers**
