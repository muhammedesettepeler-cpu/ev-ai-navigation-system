"""
Chat Routes - AI Chatbot endpoints for EV navigation assistance
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import logging
import time

logger = logging.getLogger(__name__)
router = APIRouter()

class ChatMessage(BaseModel):
    message: str
    context_type: Optional[str] = None
    user_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    confidence: float
    sources: List[Dict[str, Any]] = []
    response_time_ms: int
    suggestions: List[str] = []

# Mock RAG system for now
class MockRAGSystem:
    def __init__(self):
        self.knowledge_base = {
            "charging": [
                "Tesla Superchargers are compatible with Tesla vehicles and provide up to 250kW charging speed.",
                "CCS (Combined Charging System) is widely adopted by European and American EV manufacturers.",
                "CHAdeMO is primarily used by Nissan and some other Japanese manufacturers.",
                "Level 3 DC fast charging can charge most EVs to 80% in 30-45 minutes."
            ],
            "vehicles": [
                "Tesla Model S has a range of up to 650km and supports 250kW fast charging.",
                "BMW iX offers 610km range with 195kW charging capability.",
                "Mercedes EQS provides up to 770km range with excellent efficiency.",
                "Volkswagen ID.4 is a practical SUV with 442km range and 135kW charging."
            ],
            "routes": [
                "Plan charging stops at 20-80% battery levels for optimal charging speed.",
                "Consider weather conditions as cold temperatures can reduce EV range by 20-30%.",
                "Mountain routes require more energy due to elevation changes.",
                "Highway driving typically consumes more energy than city driving for EVs."
            ]
        }
    
    async def query(self, message: str, context_type: Optional[str] = None) -> Dict[str, Any]:
        """Mock RAG query"""
        start_time = time.time()
        
        # Simple keyword matching
        message_lower = message.lower()
        relevant_info = []
        
        # Check for charging-related queries
        if any(word in message_lower for word in ['charg', 'station', 'power', 'connector']):
            relevant_info.extend(self.knowledge_base["charging"])
        
        # Check for vehicle-related queries  
        if any(word in message_lower for word in ['vehicle', 'car', 'model', 'range', 'tesla', 'bmw', 'mercedes']):
            relevant_info.extend(self.knowledge_base["vehicles"])
        
        # Check for route-related queries
        if any(word in message_lower for word in ['route', 'trip', 'plan', 'drive', 'travel']):
            relevant_info.extend(self.knowledge_base["routes"])
        
        # Generate response
        if relevant_info:
            response = f"Based on your question about EV navigation, here's what I can tell you:\n\n"
            response += "\n".join([f"• {info}" for info in relevant_info[:3]])
            confidence = 0.8
        else:
            response = "I can help you with electric vehicle navigation, charging stations, vehicle specifications, and route planning. What would you like to know?"
            confidence = 0.6
        
        response_time = int((time.time() - start_time) * 1000)
        
        return {
            "response": response,
            "confidence": confidence,
            "sources": [{"text": info, "score": 0.8} for info in relevant_info[:2]],
            "response_time_ms": response_time
        }

# Dependency injection
def get_rag_system():
    return MockRAGSystem()

@router.post("/ask", response_model=ChatResponse)
async def ask_question(
    chat_message: ChatMessage,
    rag_system = Depends(get_rag_system)
):
    """
    Ask a question to the EV navigation AI assistant
    """
    try:
        logger.info(f"Processing chat query: {chat_message.message[:100]}...")
        
        # Query the RAG system
        result = await rag_system.query(
            message=chat_message.message,
            context_type=chat_message.context_type
        )
        
        # Generate suggestions based on the query
        suggestions = generate_suggestions(chat_message.message)
        
        response = ChatResponse(
            response=result["response"],
            confidence=result["confidence"],
            sources=result["sources"],
            response_time_ms=result["response_time_ms"],
            suggestions=suggestions
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Chat query failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Chat processing failed: {str(e)}")

@router.get("/suggestions")
async def get_chat_suggestions():
    """
    Get suggested questions for the chat interface
    """
    return {
        "suggestions": [
            "How do I plan a long-distance trip in my Tesla Model 3?",
            "What are the best charging networks for cross-country travel?",
            "How does cold weather affect EV battery range?",
            "What's the difference between CCS and CHAdeMO charging?",
            "Which EV has the longest range for highway driving?",
            "How long does it take to charge at different power levels?",
            "What should I consider when buying my first electric car?",
            "How do I find charging stations along my route?"
        ],
        "categories": [
            {"name": "Route Planning", "queries": [
                "Plan route from [city] to [city]",
                "Best charging stops for long trips",
                "How to optimize charging schedule"
            ]},
            {"name": "Charging", "queries": [
                "Charging network comparison",
                "Fast charging vs slow charging",
                "Charging costs by network"
            ]},
            {"name": "Vehicles", "queries": [
                "Compare EV models",
                "Best EV for families",
                "Most efficient electric cars"
            ]}
        ]
    }

@router.get("/conversation-starters")
async def get_conversation_starters():
    """
    Get conversation starter prompts
    """
    return {
        "starters": [
            {
                "title": "Plan Your First EV Road Trip",
                "prompt": "I'm planning my first long-distance trip in an electric vehicle. Can you help me understand what I need to know?",
                "category": "route_planning"
            },
            {
                "title": "Compare Charging Networks", 
                "prompt": "What are the differences between Tesla Supercharger, Electrify America, and other charging networks?",
                "category": "charging"
            },
            {
                "title": "Choose the Right EV",
                "prompt": "I'm looking to buy an electric car. What factors should I consider for my daily commute and weekend trips?",
                "category": "vehicles"
            },
            {
                "title": "Winter Driving Tips",
                "prompt": "How does cold weather affect electric vehicle performance and what can I do to maximize range in winter?",
                "category": "tips"
            }
        ]
    }

def generate_suggestions(query: str) -> List[str]:
    """Generate follow-up suggestions based on user query"""
    query_lower = query.lower()
    suggestions = []
    
    if 'charg' in query_lower:
        suggestions.extend([
            "How long does charging take at different power levels?",
            "What's the cost difference between charging networks?",
            "How do I find the fastest charging stations?"
        ])
    
    if any(word in query_lower for word in ['route', 'trip', 'plan']):
        suggestions.extend([
            "How do I account for elevation changes in my route?",
            "What's the optimal battery level for starting a trip?",
            "Should I charge to 100% for long trips?"
        ])
    
    if any(word in query_lower for word in ['vehicle', 'car', 'buy']):
        suggestions.extend([
            "What's the difference in efficiency between EV models?",
            "Which EVs have the fastest charging speeds?",
            "What size battery do I need for my driving habits?"
        ])
    
    # Return up to 3 suggestions
    return suggestions[:3]