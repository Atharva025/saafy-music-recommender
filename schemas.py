"""
Pydantic models for request/response validation and type safety
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict


class ImageQuality(BaseModel):
    """Image URL with quality indicator"""
    quality: str
    url: str


class Artist(BaseModel):
    """Artist information"""
    id: str
    name: str
    role: Optional[str] = None
    type: Optional[str] = None
    image: Optional[List[ImageQuality]] = None
    url: Optional[str] = None


class ArtistGroup(BaseModel):
    """Grouped artists by category"""
    primary: List[Artist] = []
    featured: List[Artist] = []
    all: List[Artist] = []


class Album(BaseModel):
    """Album information"""
    id: Optional[str] = None
    name: Optional[str] = None
    url: Optional[str] = None


class DownloadUrl(BaseModel):
    """Download URL with quality indicator"""
    quality: str
    url: str


class SongResponse(BaseModel):
    """Complete song data structure from Saafy API"""
    id: str
    name: str
    type: Optional[str] = None
    year: Optional[str] = None
    releaseDate: Optional[str] = None
    duration: Optional[int] = None
    label: Optional[str] = None
    explicitContent: Optional[bool] = False
    playCount: Optional[int] = None
    language: Optional[str] = None
    hasLyrics: Optional[bool] = False
    lyricsId: Optional[str] = None
    url: Optional[str] = None
    copyright: Optional[str] = None
    album: Optional[Album] = None
    artists: Optional[ArtistGroup] = None
    image: Optional[List[ImageQuality]] = None
    downloadUrl: Optional[List[DownloadUrl]] = None


class SearchResults(BaseModel):
    """Search results container"""
    total: int
    start: int
    results: List[SongResponse]


class SearchResponse(BaseModel):
    """API response for search endpoint"""
    success: bool
    data: SearchResults


class SongDocument(BaseModel):
    """
    MongoDB document model for storing songs with embeddings
    This is what we store in our database
    """
    song_id: str = Field(..., description="Unique song identifier from Saafy API")
    name: str = Field(..., description="Song name")
    language: Optional[str] = Field(None, description="Song language")
    
    # Artist and album information
    primary_artist: str = Field(..., description="Primary artist name")
    album_name: Optional[str] = Field(None, description="Album name")
    
    # Vector embedding
    embedding: List[float] = Field(..., description="384-dimensional embedding vector")
    
    # Store the complete original response for easy retrieval
    raw_data: Dict[str, Any] = Field(..., description="Original song data from Saafy API")
    
    class Config:
        json_schema_extra = {
            "example": {
                "song_id": "abc123",
                "name": "Imagine",
                "language": "english",
                "primary_artist": "John Lennon",
                "album_name": "Imagine",
                "embedding": [0.1, 0.2, 0.3],  # truncated for example
                "raw_data": {}
            }
        }


class RecommendationResponse(BaseModel):
    """Response model for recommendations"""
    song_id: str
    name: str
    primary_artist: str
    album_name: Optional[str] = None
    language: Optional[str] = None
    similarity_score: float = Field(..., description="Cosine similarity score (0-1)")
    raw_data: Dict[str, Any]


class RecommendationsListResponse(BaseModel):
    """List of recommendations"""
    query_song_id: str
    query_song_name: str
    recommendations: List[RecommendationResponse]
    total: int


class ErrorResponse(BaseModel):
    """Standard error response"""
    success: bool = False
    error: str
    detail: Optional[str] = None
