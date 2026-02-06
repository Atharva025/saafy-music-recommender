# 🎯 Deploy to Hugging Face - Quick Start

## ✅ Files Ready
- ✓ `app.py` - Gradio interface  
- ✓ NO Docker needed!
- ✓ All configured for Gradio

## 🚀 3 Steps:

### 1. Create Space
- https://huggingface.co/new-space
- SDK: **Gradio**
- Hardware: **CPU basic (FREE)**

### 2. Add Secrets
```
MONGODB_URI = mongodb+srv://atharva070720_db_user:atharva025@music-rec-db.xhtglpb.mongodb.net/?retryWrites=true&w=majority
MONGODB_DB_NAME = music_recommendations
SAAFY_API_BASE_URL = https://saafy-api.vercel.app/api
```

### 3. Push
```bash
git remote add hf https://huggingface.co/spaces/YOUR_USERNAME/saafy-music-recommender
git add .
git commit -m "Deploy Gradio app"
git push hf main
```

Done! Live at `https://huggingface.co/spaces/YOUR_USERNAME/saafy-music-recommender` 🎉
