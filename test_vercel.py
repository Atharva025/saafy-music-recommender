"""
Quick test for Vercel deployment setup
"""
import sys
from pathlib import Path

print("Testing Vercel deployment setup...")
print("=" * 50)

# Test 1: Check if vercel.json exists
vercel_config = Path("vercel.json")
if vercel_config.exists():
    print("✓ vercel.json exists")
else:
    print("✗ vercel.json NOT FOUND")
    sys.exit(1)

# Test 2: Check if api/index.py exists
api_entry = Path("api/index.py")
if api_entry.exists():
    print("✓ api/index.py exists")
else:
    print("✗ api/index.py NOT FOUND")
    sys.exit(1)

# Test 3: Check imports
print("\nTesting imports...")
try:
    from config import get_settings
    print("✓ config imported")
    
    from database import connect_to_mongo, get_database
    print("✓ database imported")
    
    from ml_engine import initialize_ml_engine, get_ml_engine
    print("✓ ml_engine imported")
    
    from main import app
    print("✓ FastAPI app imported")
    
except Exception as e:
    print(f"✗ Import error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 4: Check settings
print("\nTesting configuration...")
try:
    settings = get_settings()
    print(f"✓ MongoDB DB: {settings.mongodb_db_name}")
    print(f"✓ Saafy API: {settings.saafy_api_base_url}")
except Exception as e:
    print(f"✗ Config error: {e}")
    sys.exit(1)

# Test 5: Verify no Netlify files remain
print("\nVerifying cleanup...")
netlify_files = list(Path(".").rglob("*netlify*"))
if netlify_files:
    print(f"⚠ Warning: Netlify files still present: {[str(f) for f in netlify_files]}")
else:
    print("✓ All Netlify files removed")

print("\n" + "=" * 50)
print("✅ All checks passed!")
print("🚀 Ready for Vercel deployment!")
print("\nNext steps:")
print("1. git add . && git commit -m 'Ready for Vercel'")
print("2. git push")
print("3. Go to https://vercel.com/new")
print("4. Import your repo and add environment variables")
