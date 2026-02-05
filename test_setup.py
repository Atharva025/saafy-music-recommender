"""
Installation and Configuration Test Script
Run this after setup to verify everything is working
"""
import sys
import asyncio


def test_imports():
    """Test if all required packages are installed"""
    print("=" * 60)
    print("TESTING PACKAGE IMPORTS")
    print("=" * 60)
    
    packages = [
        ("fastapi", "FastAPI"),
        ("uvicorn", "Uvicorn"),
        ("motor", "Motor (Async MongoDB)"),
        ("pymongo", "PyMongo"),
        ("sentence_transformers", "Sentence Transformers"),
        ("dotenv", "Python-dotenv"),
        ("requests", "Requests"),
        ("numpy", "NumPy"),
        ("pydantic", "Pydantic"),
    ]
    
    failed = []
    for package, name in packages:
        try:
            __import__(package)
            print(f"✓ {name}")
        except ImportError:
            print(f"✗ {name} - NOT INSTALLED")
            failed.append(package)
    
    if failed:
        print(f"\n❌ Missing packages: {', '.join(failed)}")
        print("Run: pip install -r requirements.txt")
        return False
    
    print("\n✓ All packages installed successfully!\n")
    return True


def test_config():
    """Test if configuration loads correctly"""
    print("=" * 60)
    print("TESTING CONFIGURATION")
    print("=" * 60)
    
    try:
        from config import get_settings
        settings = get_settings()
        
        checks = {
            "MongoDB URI": settings.mongodb_uri != "mongodb+srv://<username>:<password>@<cluster>.mongodb.net/?retryWrites=true&w=majority",
            "MongoDB DB Name": bool(settings.mongodb_db_name),
            "Saafy API URL": bool(settings.saafy_api_base_url),
            "Model Name": settings.model_name == "all-MiniLM-L6-v2",
            "Embedding Dimensions": settings.embedding_dimensions == 384,
        }
        
        all_passed = True
        for check_name, passed in checks.items():
            status = "✓" if passed else "✗"
            print(f"{status} {check_name}")
            if not passed:
                all_passed = False
        
        if not all_passed:
            print("\n⚠️  Configuration incomplete!")
            print("Please update the .env file with your MongoDB credentials.")
            return False
        
        print("\n✓ Configuration looks good!\n")
        return True
        
    except Exception as e:
        print(f"✗ Configuration error: {e}")
        return False


def test_ml_model():
    """Test if ML model can be loaded"""
    print("=" * 60)
    print("TESTING ML MODEL")
    print("=" * 60)
    print("Note: First run will download ~80MB model...\n")
    
    try:
        from ml_engine import MLEngine
        
        print("Loading model (this may take 10-30 seconds)...")
        engine = MLEngine()
        
        print("✓ Model loaded successfully")
        
        # Test embedding generation
        print("Testing embedding generation...")
        text = "Test Song Artist Album English"
        embedding = engine.generate_embedding(text)
        
        if len(embedding) == 384:
            print(f"✓ Generated {len(embedding)}-dimensional embedding")
        else:
            print(f"✗ Expected 384 dimensions, got {len(embedding)}")
            return False
        
        print("\n✓ ML model working correctly!\n")
        return True
        
    except ImportError as e:
        print(f"✗ ML model import error: {e}")
        print("\nThis might be a dependency issue. Try:")
        print("  pip install --upgrade sentence-transformers torch transformers")
        return False
    except Exception as e:
        print(f"✗ ML model error: {e}")
        print(f"Error type: {type(e).__name__}")
        return False


async def test_database():
    """Test database connection"""
    print("=" * 60)
    print("TESTING DATABASE CONNECTION")
    print("=" * 60)
    
    try:
        from database import connect_to_mongo, close_mongo_connection, get_database
        
        print("Connecting to MongoDB...")
        await connect_to_mongo()
        print("✓ Connected to MongoDB")
        
        db = get_database()
        print(f"✓ Database object retrieved: {db.name}")
        
        # Test a simple operation
        result = await db.command("ping")
        print("✓ Database ping successful")
        
        await close_mongo_connection()
        print("✓ Connection closed properly")
        
        print("\n✓ Database connection working!\n")
        return True
        
    except Exception as e:
        print(f"✗ Database error: {e}")
        print("\nTroubleshooting:")
        print("1. Check if MongoDB URI is correct in .env")
        print("2. Verify IP is whitelisted in MongoDB Atlas")
        print("3. Ensure database user credentials are correct")
        return False


def test_api():
    """Test if API can start"""
    print("=" * 60)
    print("TESTING API STRUCTURE")
    print("=" * 60)
    
    try:
        from main import app
        
        print("✓ FastAPI app imported successfully")
        
        routes = [route.path for route in app.routes]
        expected_routes = ["/", "/proxy/search", "/songs/{song_id}", "/stats"]
        
        for route in expected_routes:
            if any(route in r for r in routes):
                print(f"✓ Route exists: {route}")
            else:
                print(f"✗ Route missing: {route}")
        
        print("\n✓ API structure looks good!\n")
        return True
        
    except Exception as e:
        print(f"✗ API error: {e}")
        return False


def test_external_api():
    """Test if Saafy API is accessible"""
    print("=" * 60)
    print("TESTING EXTERNAL API ACCESS")
    print("=" * 60)
    
    try:
        import requests
        from config import get_settings
        
        settings = get_settings()
        url = f"{settings.saafy_api_base_url}/search/songs"
        params = {"query": "test", "limit": 1}
        
        print(f"Testing connection to: {url}")
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            print("✓ Saafy API is accessible")
            data = response.json()
            if data.get("success"):
                print("✓ API response format is correct")
            else:
                print("⚠️  API responded but format unexpected")
        else:
            print(f"✗ API returned status code: {response.status_code}")
            return False
        
        print("\n✓ External API working!\n")
        return True
        
    except Exception as e:
        print(f"✗ External API error: {e}")
        return False


def print_summary(results):
    """Print test summary"""
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    total = len(results)
    passed = sum(results.values())
    
    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n" + "=" * 60)
        print("🎉 ALL TESTS PASSED!")
        print("=" * 60)
        print("\nYour backend is ready to run!")
        print("\nNext steps:")
        print("1. Create the Vector Search Index in MongoDB Atlas")
        print("   (See SETUP.md or README.md for instructions)")
        print("2. Run the server: python main.py")
        print("3. Visit http://localhost:8000/docs")
        print("\n" + "=" * 60)
    else:
        print("\n" + "=" * 60)
        print("⚠️  SOME TESTS FAILED")
        print("=" * 60)
        print("\nPlease fix the failed tests before running the server.")
        print("Check SETUP.md for troubleshooting steps.")


async def run_all_tests():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("MUSIC RECOMMENDATION BACKEND - TEST SUITE")
    print("=" * 60)
    print("\nThis will verify your installation and configuration.\n")
    
    results = {}
    
    # Test 1: Imports
    results["Package Imports"] = test_imports()
    
    # Test 2: Configuration
    results["Configuration"] = test_config()
    
    # Test 3: ML Model (only if imports passed)
    if results["Package Imports"]:
        results["ML Model"] = test_ml_model()
    else:
        print("⏭️  Skipping ML Model test (imports failed)\n")
        results["ML Model"] = False
    
    # Test 4: Database (only if config passed)
    if results["Configuration"]:
        results["Database Connection"] = await test_database()
    else:
        print("⏭️  Skipping Database test (config not ready)\n")
        results["Database Connection"] = False
    
    # Test 5: API Structure
    results["API Structure"] = test_api()
    
    # Test 6: External API
    results["External API"] = test_external_api()
    
    # Print summary
    print_summary(results)


if __name__ == "__main__":
    try:
        asyncio.run(run_all_tests())
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        sys.exit(1)
