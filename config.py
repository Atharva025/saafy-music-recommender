"""
Configuration management using pydantic-settings
Loads environment variables from .env file
"""
from pydantic_settings import BaseSettings
from functools import lru_cache
from urllib.parse import quote_plus
import re


def fix_mongodb_uri(uri: str) -> str:
    """
    Automatically escape username and password in MongoDB URI if needed.
    Handles URIs with unescaped special characters.
    
    Args:
        uri: MongoDB connection string
        
    Returns:
        Properly escaped MongoDB URI
    """
    # Pattern to extract username and password from URI
    pattern = r'mongodb\+srv://([^:]+):([^@]+)@(.+)'
    match = re.match(pattern, uri)
    
    if match:
        username, password, rest = match.groups()
        
        # URL encode username and password if they contain special characters
        # Only encode if not already encoded
        if '%' not in username:
            username_encoded = quote_plus(username)
        else:
            username_encoded = username
            
        if '%' not in password:
            password_encoded = quote_plus(password)
        else:
            password_encoded = password
        
        # Reconstruct the URI with encoded credentials
        return f"mongodb+srv://{username_encoded}:{password_encoded}@{rest}"
    
    # If pattern doesn't match, return as-is (might be already correct or different format)
    return uri


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # MongoDB Configuration
    mongodb_uri: str
    mongodb_db_name: str
    
    # External API Configuration
    saafy_api_base_url: str
    
    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    
    # ML Model Configuration
    model_name: str = "all-MiniLM-L6-v2"
    embedding_dimensions: int = 384
    
    def __init__(self, **kwargs):
        """Initialize and automatically fix MongoDB URI"""
        super().__init__(**kwargs)
        # Automatically escape MongoDB credentials
        self.mongodb_uri = fix_mongodb_uri(self.mongodb_uri)
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """
    Returns cached settings instance
    lru_cache ensures we only load settings once
    """
    return Settings()
