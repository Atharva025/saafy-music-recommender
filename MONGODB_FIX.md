# 🔧 Fix MongoDB Connection Issue

## Your Current Problem

Your `.env` file had an incorrect MongoDB URI format:
```
❌ WRONG: mongodb+srv://atharva070720_db_user@admin:atharva070720_db_user@music-rec-db...
```

The correct format is:
```
✅ CORRECT: mongodb+srv://USERNAME:PASSWORD@CLUSTER/
```

## What I Fixed

1. **Updated `.env`** - Fixed the URI format
2. **Updated `config.py`** - Added automatic URL encoding for special characters
3. **Created `mongodb_helper.py`** - Tool to help build/validate URIs

## 🚀 Quick Fix Instructions

### Step 1: Get Your Actual MongoDB Password

The `.env` file now has `YOUR_PASSWORD` as a placeholder. You need to replace it with your actual MongoDB password.

**To get your password:**
1. Go to MongoDB Atlas Dashboard
2. Click "Database Access" (left sidebar)
3. Find user `atharva070720_db_user`
4. If you forgot the password, click "Edit" → "Edit Password" → Generate new password
5. **Copy the password**

### Step 2: Update Your `.env` File

Open `.env` and replace `YOUR_PASSWORD` with your actual password:

```env
MONGODB_URI=mongodb+srv://atharva070720_db_user:YOUR_ACTUAL_PASSWORD@music-rec-db.xhtglpb.mongodb.net/?retryWrites=true&w=majority
```

**Example:**
If your password is `MyPass@123`, your URI should be:
```env
MONGODB_URI=mongodb+srv://atharva070720_db_user:MyPass@123@music-rec-db.xhtglpb.mongodb.net/?retryWrites=true&w=majority
```

**Don't worry about special characters like `@`, `:`, etc.** - The backend now automatically encodes them!

### Step 3: Use the Helper Tool (Optional)

If you want to double-check your URI or build a new one:

```powershell
python mongodb_helper.py
```

Choose option 1 to build a new URI or option 2 to validate your existing one.

### Step 4: Test the Connection

```powershell
python test_setup.py
```

You should see:
```
✓ Database connection
✓ All tests passing!
```

## 🔍 Common Issues & Solutions

### Issue 1: "Authentication failed"
**Cause:** Wrong password or username
**Fix:** 
1. Verify username is `atharva070720_db_user`
2. Reset password in MongoDB Atlas if needed
3. Update `.env` with correct password

### Issue 2: "Connection timeout"
**Cause:** IP not whitelisted
**Fix:**
1. Go to MongoDB Atlas → Network Access
2. Click "Add IP Address"
3. Select "Allow Access from Anywhere" (0.0.0.0/0)

### Issue 3: "Network error"
**Cause:** Cluster name wrong or cluster not running
**Fix:**
1. Verify cluster is `music-rec-db.xhtglpb.mongodb.net`
2. Check cluster is running in MongoDB Atlas
3. Try the connection string from "Connect" button in Atlas

### Issue 4: Password has special characters
**No action needed!** The backend now automatically URL-encodes them.

Special characters that are automatically handled:
- `@` → `%40`
- `:` → `%3A`
- `/` → `%2F`
- `?` → `%3F`
- `#` → `%23`
- And many more...

## 📝 Final URI Format

Your `.env` should look like this (with your actual password):

```env
# MongoDB Atlas Configuration
# Format: mongodb+srv://USERNAME:PASSWORD@CLUSTER/
# If your password has special characters like @, :, /, etc., they will be auto-escaped
MONGODB_URI=mongodb+srv://atharva070720_db_user:YOUR_ACTUAL_PASSWORD@music-rec-db.xhtglpb.mongodb.net/?retryWrites=true&w=majority
MONGODB_DB_NAME=music_recommendations

# Saafy API Base URL
SAAFY_API_BASE_URL=https://saafy-api.vercel.app/api

# Server Configuration
HOST=0.0.0.0
PORT=8000
```

## ✅ Verification Checklist

- [ ] Username is correct: `atharva070720_db_user`
- [ ] Password is your actual MongoDB password (not `YOUR_PASSWORD`)
- [ ] Cluster address is: `music-rec-db.xhtglpb.mongodb.net`
- [ ] IP is whitelisted in MongoDB Atlas (Network Access)
- [ ] Database user exists and has read/write permissions
- [ ] `.env` file is in the project root directory

## 🎯 Next Steps After MongoDB Works

Once `python test_setup.py` shows all tests passing:

1. **Create Vector Search Index** (see SETUP.md step 5)
2. **Start the server:** `python main.py`
3. **Test the API:** Visit http://localhost:8000/docs
4. **Integrate with frontend**

---

**Need Help?**
Run `python mongodb_helper.py` for interactive assistance with your MongoDB URI.
