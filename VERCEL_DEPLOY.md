# 🚀 Vercel Deployment Guide

Your app is ready for Vercel deployment! Vercel has native FastAPI support and is much better than Netlify for Python backends.

## ✨ Why Vercel is Better

- ✅ Native Python/FastAPI support (no adapters needed)
- ✅ 10s timeout (free) / 60s (Pro)
- ✅ Better memory handling for ML models
- ✅ Simpler configuration
- ✅ Auto-detects FastAPI
- ✅ Better for serverless Python

## 📋 Deployment Steps

### Option 1: Deploy via GitHub (Recommended)

1. **Push to GitHub**
   ```bash
   git init
   git add .
   git commit -m "Deploy to Vercel"
   git remote add origin YOUR_GITHUB_REPO_URL
   git push -u origin main
   ```

2. **Connect to Vercel**
   - Go to https://vercel.com
   - Click "Add New Project"
   - Import your GitHub repository
   - Vercel auto-detects the configuration from `vercel.json`

3. **Add Environment Variables**
   
   In Vercel dashboard → Settings → Environment Variables, add:
   
   | Variable | Value | Environment |
   |----------|-------|-------------|
   | `MONGODB_URI` | `mongodb+srv://atharva070720_db_user:atharva025@music-rec-db.xhtglpb.mongodb.net/` | Production, Preview, Development |
   | `MONGODB_DB_NAME` | `music_recommendations` | Production, Preview, Development |
   | `SAAFY_API_BASE_URL` | `https://saafy-api.vercel.app/api` | Production, Preview, Development |

   **Important:** Mark `MONGODB_URI` as sensitive (click the eye icon)

4. **Deploy!**
   - Click "Deploy"
   - Wait for build to complete (~2-3 minutes)
   - Your API will be live at `https://your-project.vercel.app`

### Option 2: Deploy via Vercel CLI

```bash
# Install Vercel CLI
npm install -g vercel

# Login
vercel login

# Deploy
vercel

# Set environment variables
vercel env add MONGODB_URI
vercel env add MONGODB_DB_NAME
vercel env add SAAFY_API_BASE_URL

# Deploy to production
vercel --prod
```

## 🔗 Your API Endpoints

After deployment, your API will be available at:

```
https://your-project.vercel.app/
https://your-project.vercel.app/proxy/search?query=test&limit=10
https://your-project.vercel.app/recommend/{song_id}?limit=10
https://your-project.vercel.app/songs/{song_id}
https://your-project.vercel.app/stats
```

## 🧪 Test Locally

```bash
# Install Vercel CLI
npm install -g vercel

# Install dependencies
pip install -r requirements.txt

# Run locally with Vercel dev server
vercel dev
```

Your API will be at http://localhost:3000

## ⚙️ Configuration Files

- **vercel.json** - Main configuration
- **api/index.py** - Serverless function entry point
- **.vercelignore** - Files to exclude from deployment

## ⚠️ Known Limitations (Free Tier)

1. **10-second execution timeout** - First request (cold start) loads ML model (~3-5s)
2. **1GB memory limit** - Should be sufficient for your sentence-transformers model
3. **Background tasks** - Limited support, `/proxy/search` ingestion may be affected

### If You Hit Limits:

**Option A: Optimize**
- Reduce model size
- Use lighter embedding model
- Cache embeddings more aggressively

**Option B: Upgrade**
- Vercel Pro: $20/month
  - 60s timeout (much better!)
  - 3GB memory
  - Better for ML workloads

**Option C: Switch Platform**
- Railway.app: Free 512MB RAM, no timeout limits
- Fly.io: Free 256MB RAM, persistent VMs
- Both better suited for ML backends with long-running processes

## 🔧 Troubleshooting

### Build Fails
- Check Python version matches runtime.txt (3.11)
- Verify all dependencies in requirements.txt
- Check Vercel build logs for errors

### Function Timeout (10s)
- ML model loading takes 3-5s on cold start
- Consider upgrading to Pro for 60s timeout
- Or use Railway.app for no timeout limits

### Import Errors
- Ensure api/index.py path setup is correct
- Check that all .py files are in root or properly imported

### MongoDB Connection Issues
- Verify environment variables are set
- Check MongoDB Atlas network access (allow 0.0.0.0/0)
- Test connection locally first

### Background Tasks Not Working
- Vercel serverless functions terminate after response
- Consider using a queue service (Vercel KV, Redis, etc.)
- Or make ingestion synchronous (slower but reliable)

## 💡 Pro Tips

1. **Environment Variables**: Set them for "Production, Preview, Development" to work in all contexts
2. **Cold Starts**: First request after inactivity will be slower (3-5s for model loading)
3. **Logs**: Check Vercel dashboard logs for debugging
4. **Custom Domain**: Free custom domain support in Vercel
5. **Auto-Deploy**: Every push to main branch auto-deploys

## 📊 Free Tier Limits

- 100 GB-hours compute time/month
- 100 GB bandwidth/month
- 6,000 builds/month
- Should be plenty for personal projects!

## 🚀 Next Steps

1. Deploy to Vercel
2. Test all endpoints
3. Update your frontend to use new Vercel URL
4. Monitor usage in Vercel dashboard
5. Consider Railway.app if you need more compute time

---

**Questions?** Check Vercel docs: https://vercel.com/docs/functions/python
