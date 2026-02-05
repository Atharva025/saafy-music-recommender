# 🚀 Quick Start - Music Recommendation Backend

## ✅ What's Done
- ✅ All packages installed successfully
- ✅ ML model (all-MiniLM-L6-v2) downloaded and working
- ✅ API structure configured
- ✅ Configuration loaded
- ✅ Saafy API accessible

## ⚠️ Next Steps (Required)

### 1. Setup MongoDB Atlas (15 minutes)

**Create Free Account:**
1. Go to https://www.mongodb.com/cloud/atlas
2. Sign up (no credit card needed)
3. Create a free M0 cluster

**Get Your Connection String:**
1. Click "Connect" on your cluster
2. Choose "Connect your application"
3. Copy the connection string (looks like: `mongodb+srv://username:password@...`)

**Whitelist Your IP:**
1. Go to "Network Access" (left sidebar)
2. Click "Add IP Address"
3. Select "Allow Access from Anywhere" (0.0.0.0/0)

**Create Database User:**
1. Go to "Database Access"
2. Click "Add New Database User"
3. Username: `musicapp` (or your choice)
4. Password: Generate strong password and **save it**
5. Select "Read and write to any database"

### 2. Update Your `.env` File

Edit the `.env` file in this directory:

```env
MONGODB_URI=mongodb+srv://YOUR_USERNAME:YOUR_PASSWORD@YOUR_CLUSTER.mongodb.net/?retryWrites=true&w=majority
MONGODB_DB_NAME=music_recommendations
SAAFY_API_BASE_URL=https://saafy-api.vercel.app/api
HOST=0.0.0.0
PORT=8000
```

**Replace:**
- `YOUR_USERNAME` → your MongoDB username (e.g., `musicapp`)
- `YOUR_PASSWORD` → your MongoDB password
- `YOUR_CLUSTER` → your cluster address (e.g., `cluster0.abc123.mongodb.net`)

### 3. Create Vector Search Index in MongoDB Atlas

**⚠️ CRITICAL - The recommendation feature won't work without this!**

1. In MongoDB Atlas, go to your cluster
2. Click "Search" tab (in left sidebar)
3. Click "Create Search Index"
4. Select "JSON Editor"
5. Paste this configuration:

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

6. Set these values:
   - **Index Name:** `vector_index` (must be exactly this!)
   - **Database:** `music_recommendations`
   - **Collection:** `songs`

7. Click "Create Search Index"
8. Wait ~1-2 minutes for it to become "Active" ✅

### 4. Test Again

Run the test script to verify MongoDB connection:

```powershell
python test_setup.py
```

You should see all tests passing! ✅

### 5. Start the Server

```powershell
python main.py
```

You should see:
```
INFO:     ML Engine initialized
INFO:     Database connected
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 6. Test the API

Open your browser:
- **API Documentation:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/

Try a search in your browser or PowerShell:
```powershell
curl "http://localhost:8000/proxy/search?query=Believer&limit=5"
```

After searching, copy a `song_id` from results and get recommendations:
```powershell
curl "http://localhost:8000/recommend/YOUR_SONG_ID?limit=10"
```

---

## 📖 Full Documentation

- **[README.md](README.md)** - Complete documentation with API reference
- **[SETUP.md](SETUP.md)** - Detailed setup guide with troubleshooting
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - System design and how it works

---

## 🎯 Integration with Frontend

In your frontend, replace Saafy API calls:

**Before:**
```javascript
fetch('https://saafy-api.vercel.app/api/search/songs?query=test')
```

**After:**
```javascript
fetch('http://localhost:8000/proxy/search?query=test')
```

**Get Recommendations:**
```javascript
fetch(`http://localhost:8000/recommend/${songId}?limit=10`)
```

---

## ❓ Troubleshooting

### "Authentication failed" error
- Check your MongoDB URI in `.env`
- Verify username and password are correct
- Make sure password doesn't have special characters (or URL-encode them)
- Check IP is whitelisted in MongoDB Atlas

### "Vector search failed"
- Vector Search Index not created or not active yet
- Wait 1-2 minutes after creating the index
- Verify index name is exactly `vector_index`

### "Song not analyzed yet"
- Song must be searched first before recommendations work
- Use `/proxy/search` to add songs to database

### ML model errors
- All dependencies are installed correctly (test shows ✓)
- If issues persist, try: `pip install --upgrade sentence-transformers`

---

## 🎉 You're Ready!

Once MongoDB is set up, you have a **production-ready ML-powered music recommendation backend**!

**Features:**
- 🔍 Smart search proxy with automatic data ingestion
- 🤖 AI-powered recommendations using sentence transformers
- ⚡ Fast async/await architecture
- 🎯 384-dimensional semantic embeddings
- 🔥 Background processing (non-blocking)
- 📊 MongoDB Atlas Vector Search
- 🛡️ Type-safe with Pydantic
- 📝 Comprehensive logging

**What's Next:**
1. Set up MongoDB (15 min)
2. Start the server
3. Integrate with your frontend
4. Build amazing music experiences! 🎵
