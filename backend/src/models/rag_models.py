"""
RAG System Data Models
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum

class DocumentType(str, Enum):
    MANUAL = "manual"
    FAQ = "faq" 
    ARTICLE = "article"
    CHARGING_STATION = "charging_station"
    VEHICLE_SPEC = "vehicle_spec"
    ROUTE_INFO = "route_info"
    GENERAL = "general"

class Document(BaseModel):
    """Document model for RAG system"""
    id: str = Field(..., description="Unique document identifier")
    title: str = Field(..., description="Document title")
    content: str = Field(..., description="Document content")
    document_type: DocumentType = Field(..., description="Type of document")
    metadata: Dict[str, Any] = Field(default={}, description="Additional metadata")
    source_url: Optional[str] = Field(None, description="Source URL if applicable")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class QueryResult(BaseModel):
    """Result from vector similarity search"""
    document_id: str = Field(..., description="Source document ID")
    chunk_text: str = Field(..., description="Relevant text chunk")
    score: float = Field(..., description="Similarity score (0-1)")
    metadata: Dict[str, Any] = Field(default={}, description="Chunk metadata")

class RAGQuery(BaseModel):
    """RAG query request"""
    query: str = Field(..., description="User query text")
    context_type: Optional[str] = Field(None, description="Type of context needed")
    max_results: int = Field(default=5, description="Maximum number of results")
    similarity_threshold: float = Field(default=0.7, description="Minimum similarity threshold")
    filters: Dict[str, Any] = Field(default={}, description="Additional filters")

class RAGResponse(BaseModel):
    """RAG response with generated answer and sources"""
    query: str = Field(..., description="Original query")
    response: str = Field(..., description="Generated response")
    sources: List[QueryResult] = Field(..., description="Source documents used")
    confidence: float = Field(..., description="Confidence in the response")
    response_time_ms: int = Field(..., description="Response time in milliseconds")
    metadata: Dict[str, Any] = Field(default={}, description="Additional response metadata")

class ChargingStationDocument(BaseModel):
    """Specialized document for charging stations"""
    id: str
    name: str
    network: str
    location: Dict[str, float]  # lat, lon
    address: str
    connector_types: List[str]
    charging_powers: List[int]
    amenities: List[str]
    pricing_info: Dict[str, Any]
    availability_pattern: Optional[str] = None
    reviews_summary: Optional[str] = None

class VehicleSpecDocument(BaseModel):
    """Specialized document for vehicle specifications"""
    id: str
    manufacturer: str
    model: str
    year: int
    specifications: Dict[str, Any]
    charging_info: Dict[str, Any]
    range_info: Dict[str, Any]
    efficiency_data: Dict[str, Any]
    user_reviews: Optional[str] = None

class RouteDocument(BaseModel):
    """Specialized document for route information"""
    id: str
    route_name: str
    start_location: Dict[str, Any]
    end_location: Dict[str, Any]
    distance_km: float
    terrain_type: str
    charging_stations_count: int
    difficulty_level: str
    seasonal_considerations: Optional[str] = None
    tips_and_advice: Optional[str] = None