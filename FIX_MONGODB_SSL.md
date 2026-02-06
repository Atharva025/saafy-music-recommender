# 🔧 CRITICAL: MongoDB SSL Fix for HF Spaces

## ⚠️ Action Required:

Your `MONGODB_URI` secret in HF Spaces **MUST** have these exact parameters:

```
mongodb+srv://atharva070720_db_user:atharva025@music-rec-db.xhtglpb.mongodb.net/?retryWrites=true&w=majority&tls=true&tlsAllowInvalidHostnames=false
```

### 🔑 Steps to Fix:

1. Go to your HF Space → **Settings** → **Variables and secrets**

2. Edit the `MONGODB_URI` secret

3. **Replace** with the full URI above (all in one line, no line breaks)

4. **Save**

5. **Restart** your Space (Settings → Factory reboot)

## ✅ What I Changed in Code:

- Increased timeouts (30s instead of 10s)
- Added connection pool settings
- Simplified TLS configuration for HF Spaces

## 🔍 MongoDB Atlas Checklist:

1. **Network Access:**
   - Go to Atlas Dashboard → Network Access
   - Ensure `0.0.0.0/0` is in IP Access List
   - This allows connections from anywhere (including HF Spaces)

2. **Database User:**
   - Database Access → Verify user exists
   - Username: `atharva070720_db_user`
   - Password: `atharva025`
   - Has readWrite access to `music_recommendations` database

3. **Cluster Status:**
   - Ensure cluster is running (not paused)
   - M0 (free tier) is fine

## 🧪 Test:

After updating the secret and restarting:
1. Try the **Search** function first
2. Then try **Recommendations**

The connection should work now with the proper URI parameters!
