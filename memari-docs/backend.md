# Backend Documentation

## Architecture Overview

The backend is a FastAPI application with a clean separation of concerns:

```
backend/
├── main.py           # FastAPI endpoints only (~150 lines)
├── services.py       # ChatService with tool calling logic
├── rag_engine.py     # Hybrid RAG with re-ranking
├── prompts.py        # System prompts and tool definitions
├── config.py         # Configuration and environment
├── models.py         # Pydantic models
└── helper-scripts/   # Indexing utilities
```

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/chat` | POST | Main chat with safety, tools, JSON response |
| `/end-session` | POST | End session and trigger background indexing |
| `/health` | GET | Health check with FAISS vector count |

---

## Chat Flow (Single API Call Pattern)

Per [Groq best practices](https://console.groq.com/docs/tool-use), we use a single-call pattern:

```
User Message
    ↓
Safety Check (LlamaGuard 4)
    ↓
LLM Call with Tools
    ↓
┌─ If tool_calls:
│   Execute tools locally
│   Add results to messages
│   Call LLM again
│   └─ Loop until no tool_calls
│
└─ Model returns final JSON response
    ↓
WhatsApp-style bubbles
```

**Key Points:**
- Model decides if tools are needed
- Tools are executed locally, results sent back
- Final response includes JSON with multiple messages
- No dual API calling - model returns answer directly

---

## Prompt Caching

Structured for optimal [Groq prompt caching](https://console.groq.com/docs/prompt-caching):

```
[SYSTEM PROMPT - Static, Cached]
[TOOL DEFINITIONS - Static, Cached]
[CONVERSATION HISTORY - Dynamic]
[USER MESSAGE - Dynamic]
```

Benefits:
- 50% cost reduction on cached tokens
- Faster responses after first request
- Tools are also cached

---

## Hybrid RAG Pipeline

### Search Strategy (75% Cosine + 25% BM25)

```python
# Dense retrieval (semantic)
dense_scores = FAISS.search(query_embedding)

# Sparse retrieval (keyword)
bm25_scores = BM25.search(query)

# Hybrid combination
final_score = 0.75 * cosine + 0.25 * bm25
```

### Re-Ranking

Using CrossEncoder (`cross-encoder/ms-marco-MiniLM-L-2-v2`):

```python
# Get more candidates than needed
candidates = hybrid_search(query, top_k=10)

# Re-rank with CrossEncoder
reranked = CrossEncoder.rank(query, candidates)

# Return top 5
return reranked[:5]
```

### Fusion Retrieval (Fallback)

When confidence < 0.7:
1. Generate 3 query variations (Cerebras LLaMA 3.1)
2. Search with all variations
3. Merge and deduplicate results

---

## Tools

| Tool | Description | When Used |
|------|-------------|-----------|
| `get_user_persona` | Read user-persona.md | User asks about themselves |
| `get_long_term_memory` | Search FAISS | Reference to past events |

---

## Safety Layer

Every message passes through LlamaGuard 4:

```python
response = groq.chat.completions.create(
    model="meta-llama/llama-guard-4-12b",
    messages=[{"role": "user", "content": message}]
)

# Returns "safe" or "unsafe\nS2"
```

Unsafe messages get a friendly Hinglish rejection.

---

## Environment Variables

```env
GROQ_API_KEY=your_groq_key
CEREBRAS_API_KEY=your_cerebras_key
```

---

## Running the Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

---

## Error Handling

### Tool Use Failed Recovery

The backend gracefully handles Groq `tool_use_failed` errors when the model incorrectly attempts to call a non-existent tool (e.g., `json`).

**Error Pattern**:
```
Error code: 400 - {'error': {
  'message': "attempted to call tool 'json' which was not in request.tools",
  'failed_generation': '{"name": "json", "arguments": {"messages": [...]}}'
}}
```

**Recovery Strategy**:
1. Detect `tool_use_failed` in error message
2. Extract `failed_generation` JSON using regex
3. Parse `arguments.messages` array
4. Return as valid `WhatsAppResponse`
5. Add to session history

This ensures users still receive valid responses even when the LLM makes tool-calling mistakes.

### Frontend Retry Logic

The frontend API client (`lib/api.ts`) implements retry logic for resilience:
- **Max retries**: 2 attempts
- **Backoff**: Exponential (500ms, 1000ms)
- **Errors handled**: Network failures, 500 errors, timeouts

---

## Running the Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Health check: `curl http://localhost:8000/health`
