# Quick Setup Guide

## Step-by-Step Setup

### 1. Create Python Virtual Environment
```powershell
cd music-rec-backend
python -m venv venv
.\venv\Scripts\activate
```

### 2. Install Dependencies
```powershell
pip install -r requirements.txt
```

This will install:
- FastAPI and Uvicorn (web framework)
- Motor and PyMongo (MongoDB drivers)
- Sentence Transformers (ML model - ~80MB download on first run)
- Other utilities

### 3. Setup MongoDB Atlas

**Create Account:**
1. Go to https://www.mongodb.com/cloud/atlas
2. Sign up for free (no credit card required)
3. Create a free M0 cluster (takes ~3-5 minutes)

**Get Connection String:**
1. Click "Connect" on your cluster
2. Choose "Connect your application"
3. Copy the connection string

**Whitelist IP:**
1. Go to "Network Access"
2. Click "Add IP Address"
3. Choose "Allow Access from Anywhere" (0.0.0.0/0) for development

**Create Database User:**
1. Go to "Database Access"
2. Add new database user with password
3. Remember these credentials!

### 4. Configure Environment

Edit the `.env` file:

```env
MONGODB_URI=mongodb+srv://YOUR_USERNAME:YOUR_PASSWORD@YOUR_CLUSTER.mongodb.net/?retryWrites=true&w=majority
MONGODB_DB_NAME=music_recommendations
SAAFY_API_BASE_URL=https://saafy-api.vercel.app/api
HOST=0.0.0.0
PORT=8000
```

**Replace:**
- `YOUR_USERNAME` - your MongoDB username
- `YOUR_PASSWORD` - your MongoDB password
- `YOUR_CLUSTER` - your cluster name (e.g., cluster0.abc123)

### 5. Create Vector Search Index

**⚠️ CRITICAL - DO THIS BEFORE RUNNING**

1. Go to MongoDB Atlas Dashboard
2. Click your cluster → "Search" tab (left sidebar)
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

6. Set values:
   - **Index Name:** `vector_index`
   - **Database:** `music_recommendations`
   - **Collection:** `songs`

7. Click "Create Search Index"
8. Wait for status to become "Active" (~1-2 minutes)

### 6. Run the Server

```powershell
python main.py
```

You should see:
```
INFO:     Started server process
INFO:     Application startup complete
INFO:     ML Engine initialized
INFO:     Database connected
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 7. Test the API

Open browser and visit:
- **API Docs:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/

Try a search:
```powershell
curl "http://localhost:8000/proxy/search?query=Believer&limit=5"
```

### 8. Get Recommendations

After searching, copy a `song_id` from the results and:

```powershell
curl "http://localhost:8000/recommend/{PASTE_SONG_ID_HERE}?limit=10"
```

## Common Issues

### Issue: `ModuleNotFoundError`
**Solution:** Make sure virtual environment is activated and dependencies installed:
```powershell
.\venv\Scripts\activate
pip install -r requirements.txt
```

### Issue: `Connection refused` to MongoDB
**Solutions:**
- Check if connection string is correct in `.env`
- Verify IP is whitelisted in MongoDB Atlas Network Access
- Test connection string in MongoDB Compass first

### Issue: `Vector search failed`
**Solution:** The vector index isn't created or not active yet. Follow step 5 carefully.

### Issue: First run is slow
**Expected:** Sentence Transformers downloads the ML model (~80MB) on first run. Subsequent runs are instant.

## Next Steps

1. **Test the endpoints** using the Swagger UI at http://localhost:8000/docs
2. **Integrate with your frontend** - replace Saafy API calls with this backend
3. **Monitor logs** - Check terminal for background processing messages
4. **Check MongoDB Atlas** - View stored songs in the "Browse Collections" tab

## Production Deployment

For deploying to production (Heroku, AWS, Azure, etc.):

1. Set environment variables in your hosting platform
2. Use production-grade MongoDB connection string
3. Update CORS origins in `main.py` to your frontend domain
4. Use multiple workers:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
   ```
5. Consider using Gunicorn with Uvicorn workers
6. Enable HTTPS/SSL

## Support

- Check logs for detailed error messages
- Review the comprehensive README.md
- Verify each setup step was completed
- Ensure Python 3.10+ is installed

---

**Ready to build amazing music recommendations! 🎵**
