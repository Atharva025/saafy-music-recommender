"""
Vercel Serverless Function Entry Point
"""
import sys
from pathlib import Path

# Add parent directory to path for imports
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

from main import app

# Vercel expects an 'app' or 'handler' export
# FastAPI app can be used directly with Vercel's Python runtime
