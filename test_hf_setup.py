"""
Test Hugging Face Spaces deployment setup
"""
import sys
from pathlib import Path

print("🤗 Testing Hugging Face Spaces Setup")
print("=" * 60)

# Check required files
required_files = [
    "Dockerfile",
    "README.md",
    ".dockerignore",
    "requirements.txt",
    "main.py",
    "config.py",
    "database.py",
    "ml_engine.py",
    "schemas.py"
]

missing = []
for file in required_files:
    if Path(file).exists():
        print(f"✓ {file}")
    else:
        print(f"✗ {file} MISSING")
        missing.append(file)

if missing:
    print(f"\n❌ Missing files: {missing}")
    sys.exit(1)

# Check README doesn't contain secrets
print("\n🔒 Checking README for secrets...")
readme = Path("README.md").read_text(encoding="utf-8")

secrets_to_check = [
    "mongodb+srv://",
    "atharva070720",
    "atharva025",
    "@music-rec-db"
]

found_secrets = []
for secret in secrets_to_check:
    if secret in readme:
        found_secrets.append(secret)

if found_secrets:
    print(f"⚠️  WARNING: Found potential secrets in README: {found_secrets}")
    print("   (This might be intentional if they're examples)")
else:
    print("✓ No secrets found in README")

# Check Dockerfile
print("\n🐳 Checking Dockerfile...")
dockerfile = Path("Dockerfile").read_text(encoding="utf-8")

if "EXPOSE 7860" in dockerfile:
    print("✓ Port 7860 exposed (HF Spaces default)")
else:
    print("✗ Port 7860 not exposed")

if "uvicorn" in dockerfile:
    print("✓ Uvicorn command present")
else:
    print("✗ Uvicorn command missing")

# Test imports
print("\n📦 Testing imports...")
try:
    from config import get_settings
    print("✓ config imported")
    
    from database import connect_to_mongo
    print("✓ database imported")
    
    from ml_engine import initialize_ml_engine
    print("✓ ml_engine imported")
    
    from main import app
    print("✓ FastAPI app imported")
    
except Exception as e:
    print(f"✗ Import error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
print("✅ All checks passed!")
print("🚀 Ready for Hugging Face Spaces deployment!")
print("\nNext steps:")
print("1. Create Space at https://huggingface.co/new-space")
print("2. Add secrets (MONGODB_URI, MONGODB_DB_NAME, SAAFY_API_BASE_URL)")
print("3. git remote add hf https://huggingface.co/spaces/YOUR_USERNAME/YOUR_SPACE")
print("4. git push hf main")
print("\nCheck DEPLOY_HF.md for full guide!")
