"""
models.py - Pydantic Models for API Requests and Responses

Defines structured data models for:
- Chat requests/responses (WhatsApp-style bubbles)
- Tool execution results
- Memory and persona updates
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


# ==============================================================================
# CHAT MODELS
# ==============================================================================

class ChatRequest(BaseModel):
    """Incoming chat message from the user."""
    
    session_id: str = Field(..., description="Unique session identifier")
    message: str = Field(..., description="User's message text")
    timestamp: Optional[datetime] = Field(default_factory=datetime.now)


class WhatsAppResponse(BaseModel):
    """
    Structured response with multiple message bubbles.
    
    Ari responds like a human on WhatsApp - multiple short messages
    instead of one long paragraph.
    """
    
    messages: List[str] = Field(
        ..., 
        description="List of message bubbles to display sequentially"
    )
    tool_calls_made: Optional[List[str]] = Field(
        default=None,
        description="Names of tools that were called (for debug panel)"
    )
    retrieved_context: Optional[str] = Field(
        default=None,
        description="Context retrieved from memory (for debug panel)"
    )
    reasoning: Optional[str] = Field(
        default=None,
        description="Model's reasoning steps (for debug panel)"
    )


# ==============================================================================
# TOOL MODELS
# ==============================================================================

class ToolCallResult(BaseModel):
    """Result from executing a tool call."""
    
    tool_name: str = Field(..., description="Name of the tool that was called")
    result: str = Field(..., description="Result/output from the tool")
    execution_time_ms: Optional[float] = Field(
        default=None,
        description="How long the tool took to execute (milliseconds)"
    )


class MemoryQuery(BaseModel):
    """Query for searching long-term memory."""
    
    query: str = Field(..., description="Search query text")
    top_k: int = Field(default=5, description="Number of results to retrieve")
    use_fusion: bool = Field(
        default=False,
        description="Force fusion retrieval even if confidence is high"
    )


class MemoryResult(BaseModel):
    """Result from memory search."""
    
    chunks: List[str] = Field(..., description="Retrieved memory chunks")
    scores: List[float] = Field(..., description="Similarity scores for each chunk")
    fusion_used: bool = Field(
        default=False,
        description="Whether fusion retrieval was triggered"
    )


# ==============================================================================
# INDEXING MODELS
# ==============================================================================

class SessionData(BaseModel):
    """Raw conversation session to be indexed."""
    
    session_id: str = Field(..., description="Session identifier")
    messages: List[Dict[str, str]] = Field(
        ...,
        description="List of messages with 'role' and 'content' keys"
    )
    start_time: datetime = Field(..., description="When session started")
    end_time: datetime = Field(..., description="When session ended")


class MemoryChunk(BaseModel):
    """Rewritten session chunk for indexing in FAISS."""
    
    rewritten_text: str = Field(
        ...,
        description="LLM-rewritten version optimized for retrieval"
    )
    original_text: str = Field(..., description="Original conversation text")
    timestamp: datetime = Field(..., description="When this conversation occurred")


class PersonaUpdate(BaseModel):
    """Updated user persona content."""
    
    updated_content: str = Field(
        ...,
        description="New markdown content for user-persona.md"
    )
    changes_summary: Optional[str] = Field(
        default=None,
        description="Brief summary of what changed"
    )


# ==============================================================================
# SAFETY MODELS
# ==============================================================================

class SafetyCheckResult(BaseModel):
    """Result from Llama Guard safety check."""
    
    is_safe: bool = Field(..., description="Whether content is safe")
    violation_category: Optional[str] = Field(
        default=None,
        description="Category code if unsafe (e.g., 'S2')"
    )
    raw_output: str = Field(..., description="Raw model output ('safe' or 'unsafe\\nS2')")


# ==============================================================================
# SESSION MANAGEMENT
# ==============================================================================

class EndSessionRequest(BaseModel):
    """Request to end a session and trigger indexing."""
    
    session_id: str = Field(..., description="Session to end and index")
