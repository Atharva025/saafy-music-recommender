"""
Machine Learning Engine for generating song embeddings
Uses sentence-transformers to create 384-dimensional vectors
"""
from sentence_transformers import SentenceTransformer
from typing import List
import logging

logger = logging.getLogger(__name__)


class MLEngine:
    """Handles ML model initialization and embedding generation"""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize the sentence transformer model
        
        Args:
            model_name: Name of the sentence-transformers model to use
        """
        logger.info(f"Initializing ML model: {model_name}")
        self.model = SentenceTransformer(model_name)
        logger.info("ML model loaded successfully")
    
    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding vector for given text
        
        Args:
            text: Input text to generate embedding for
            
        Returns:
            List of floats representing the 384-dimensional embedding
            (converted from numpy array to list for MongoDB compatibility)
        """
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")
        
        # Generate embedding using the model
        embedding = self.model.encode(text)
        
        # Convert numpy array to Python list for MongoDB storage
        return embedding.tolist()
    
    def create_song_text(
        self,
        name: str,
        artist: str,
        album: str = "",
        language: str = ""
    ) -> str:
        """
        Create concatenated text representation of a song
        Format: "Song Name Artist Album Language"
        
        Args:
            name: Song name
            artist: Primary artist name
            album: Album name (optional)
            language: Song language (optional)
            
        Returns:
            Concatenated string for embedding generation
        """
        parts = [name, artist]
        
        if album:
            parts.append(album)
        if language:
            parts.append(language)
        
        return " ".join(parts)


# Global instance to be initialized at startup
_ml_engine: MLEngine = None


def get_ml_engine() -> MLEngine:
    """
    Get the global ML engine instance
    
    Returns:
        MLEngine instance
        
    Raises:
        RuntimeError: If ML engine hasn't been initialized
    """
    global _ml_engine
    if _ml_engine is None:
        raise RuntimeError("ML Engine not initialized. Call initialize_ml_engine() first.")
    return _ml_engine


def initialize_ml_engine(model_name: str = "all-MiniLM-L6-v2") -> None:
    """
    Initialize the global ML engine instance
    Should be called during application startup
    
    Args:
        model_name: Name of the model to load
    """
    global _ml_engine
    _ml_engine = MLEngine(model_name)
