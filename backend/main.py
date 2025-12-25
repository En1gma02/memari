"""
main.py - FastAPI Application for Ari Chatbot

Minimal endpoint definitions - business logic is in services.py
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

from models import ChatRequest, WhatsAppResponse, EndSessionRequest, MemoryChunk
from services import get_chat_service, session_history, session_last_activity
from rag_engine import get_rag_engine

# ==============================================================================
# APP INITIALIZATION
# ==============================================================================

app = FastAPI(
    title="Ari Chatbot API",
    description="India-focused AI chatbot with infinite memory",
    version="1.0.0"
)

# CORS middleware for Streamlit frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global references (initialized on startup)
chat_service = None
rag_engine = None


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    global chat_service, rag_engine
    print("🚀 Starting Ari Chatbot API...")
    
    chat_service = get_chat_service()
    rag_engine = get_rag_engine()
    
    print("✅ Startup complete!")


# ==============================================================================
# CHAT ENDPOINT
# ==============================================================================

@app.post("/chat", response_model=WhatsAppResponse)
async def chat(request: ChatRequest) -> WhatsAppResponse:
    """
    Main chat endpoint with safety, tool calling, and structured output.
    Uses single-call pattern per Groq best practices.
    """
    try:
        response, safety_result = chat_service.chat(
            session_id=request.session_id,
            message=request.message
        )
        return response
    except Exception as e:
        print(f"❌ Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==============================================================================
# SESSION MANAGEMENT
# ==============================================================================

@app.post("/end-session")
async def end_session(
    request: EndSessionRequest,
    background_tasks: BackgroundTasks
):
    """End a session and trigger background indexing."""
    if request.session_id not in session_history:
        raise HTTPException(status_code=404, detail="Session not found")
    
    messages = session_history[request.session_id]
    
    # Add background task for indexing
    background_tasks.add_task(
        index_session,
        session_id=request.session_id,
        messages=messages
    )
    
    # Clear session
    chat_service.clear_session(request.session_id)
    
    return {
        "status": "success",
        "message": f"Session {request.session_id} ended. Indexing in progress..."
    }


def index_session(session_id: str, messages: list):
    """Background task to index a session."""
    print(f"📝 Indexing session: {session_id}")
    
    try:
        # Convert messages to text
        session_text = "\n".join([
            f"{msg['role']}: {msg['content']}"
            for msg in messages
        ])
        
        # Rewrite session
        rewritten = rag_engine.rewrite_session(session_text)
        
        # Create memory chunk
        memory_chunk = MemoryChunk(
            rewritten_text=rewritten,
            original_text=session_text,
            timestamp=datetime.now()
        )
        
        # Index in FAISS
        rag_engine.index_memory(memory_chunk)
        
        # Update user persona
        rag_engine.update_user_persona(session_text)
        
        print(f"✅ Session {session_id} indexed successfully")
    
    except Exception as e:
        print(f"❌ Error indexing session {session_id}: {e}")


# ==============================================================================
# HEALTH CHECK
# ==============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "rag_engine": rag_engine is not None,
        "faiss_vectors": rag_engine.index.ntotal if rag_engine else 0
    }


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Ari Chatbot API",
        "version": "1.0.0",
        "docs": "/docs"
    }
