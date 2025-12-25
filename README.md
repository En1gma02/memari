<p align="center">
  <h1 align="center">🧠 Memari</h1>
  <p align="center"><strong>An AI Chatbot with Infinite Long-Term Memory</strong></p>
  <p align="center">
    <em>Building human-like memory for AI conversations</em>
  </p>
</p>

---

## 🎯 Vision

**Memari** is an AI chatbot named **Ari** designed to remember conversations like a human friend would. Unlike traditional chatbots that forget context after a session ends, Ari can recall references to events discussed weeks, months, or even years ago.

> *"Talking to Ari should feel like chatting with a friend on WhatsApp who actually remembers your life."*

This project demonstrates a novel **Hybrid Memory Architecture** for solving the infinite memory problem in conversational AI.

---

## 🏗️ Architecture

Memari implements a **3-Layer Hybrid Memory System**:

```
┌─────────────────────────────────────────────────────────────────┐
│                     MEMORY ARCHITECTURE                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────┐  ┌──────────────────┐  ┌────────────────┐ │
│  │  SHORT-TERM      │  │  USER PERSONA    │  │  LONG-TERM     │ │
│  │  MEMORY          │  │  MEMORY          │  │  MEMORY        │ │
│  ├──────────────────┤  ├──────────────────┤  ├────────────────┤ │
│  │ Last 5-10 msgs   │  │ Structured MD    │  │ FAISS Vector   │ │
│  │ in context       │  │ file with user   │  │ Database with  │ │
│  │ window           │  │ facts, likes,    │  │ session-based  │ │
│  │                  │  │ personality      │  │ embeddings     │ │
│  └──────────────────┘  └──────────────────┘  └────────────────┘ │
│         ▲                      ▲                     ▲          │
│         │                      │                     │          │
│    Always Active          Tool Call            Tool Call        │
│                        get_user_persona    get_long_term_memory │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Memory Layers

| Layer | Purpose | Storage | Retrieval |
|-------|---------|---------|-----------|
| **Short-Term** | Immediate conversation context | In-memory buffer | Always included |
| **User Persona** | Facts, preferences, personality | Markdown file | Tool call |
| **Long-Term** | Historical conversations | FAISS + Embeddings | RAG Pipeline |

---

## 🔧 Tech Stack

| Component | Technology |
|-----------|------------|
| **Frontend** | Next.js 16 + React 19 + shadcn/ui + Tailwind v4 |
| **Backend** | FastAPI (Python) |
| **Vector DB** | FAISS (faiss-cpu) |
| **Embeddings** | sentence-transformers (`all-MiniLM-L6-v2`) |
| **Re-ranking** | CrossEncoder (`ms-marco-MiniLM-L-2-v2`) |
| **LLM - Fast** | Cerebras (`llama-3.1-8b`) |
| **LLM - Smart** | Groq (`gpt-oss-120b` with tool calling) |
| **Safety** | Groq (`llama-guard-4-12b`) |

---

## 📁 Project Structure

```
memari/
├── backend/
│   ├── main.py            # FastAPI endpoints (minimal)
│   ├── services.py        # ChatService with tool calling
│   ├── rag_engine.py      # Hybrid RAG (cosine + BM25 + reranking)
│   ├── prompts.py         # System prompts & tool definitions
│   ├── config.py          # Configuration & environment
│   ├── models.py          # Pydantic models
│   ├── requirements.txt
│   ├── helper-scripts/
│   │   ├── index_chat.py           # Index chat → FAISS
│   │   ├── chat_to_user_persona.py # Generate persona
│   │   └── index_to_json.py        # Export to JSON
│   ├── data/
│   │   ├── CHAT.txt
│   │   ├── user-persona.md
│   │   ├── faiss_index.bin
│   │   └── metadata.pkl
├── frontend               # Nextjs frontend
├── llm-docs/              # Cerebras & Groq API docs
├── memari-docs/           # Project documentation
├── streamlit/             # Prototype streamlit app
│   │   ├── app.py
│   │   └── requirements.txt
└── README.md
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+ with Bun
- Cerebras API Key
- Groq API Key

### 1. Clone & Setup Backend

```bash
cd backend
pip install -r requirements.txt
```

### 2. Configure Environment

Create `backend/.env`:

```env
CEREBRAS_API_KEY=your_cerebras_key
GROQ_API_KEY=your_groq_key
```

### 3. Run Backend

```bash
cd backend
uvicorn main:app --reload
```

### 4. Run Frontend

```bash
cd frontend
bun install
bun dev
```

---

## 🧪 Memory Pipeline

### Indexing Flow

```
CHAT.txt → Session Chunking → LLM Rewriting → Embeddings → FAISS + BM25
              ("Human 1: Hi")   (Cerebras)    (MiniLM)
```

### Retrieval Flow (Hybrid Search)

```
User Query
    ↓
┌─────────────────────────────────────┐
│  75% Cosine (FAISS) + 25% BM25     │
└─────────────────────────────────────┘
    ↓
CrossEncoder Re-ranking (ms-marco-MiniLM)
    ↓
Top 5 Results → LLM Context
```

### Chat Flow (Single API Call Pattern)

```
User → Safety (LlamaGuard) → LLM + Tools → Execute → Final JSON Response
```

---

## 💡 Key Features

- **Session-Based Chunking**: Conversations are split by `"Human 1: Hi"` delimiter
- **LLM-Optimized Memories**: Raw chat is rewritten for better semantic retrieval
- **Dual Metadata Storage**: Both original and rewritten text preserved
- **Tool-Based Memory Access**: Memory is retrieved only when needed via function calling
- **Latency Optimization**: Dense retrieval first, fusion only when confidence is low

---

## 📊 Current Stats

| Metric | Value |
|--------|-------|
| Total Sessions | 93 |
| Total Characters | 53,149 |
| Estimated Tokens | ~13,255 |
| Embedding Dimension | 384 |
| Index Size | ~140 KB |

---

## 🎨 Frontend Design

Inspired by Rumik AI's IRA interface:

| Pane | Content |
|------|---------|
| **Left (20%)** | Chat history database for reference |
| **Center (60%)** | Main chat interface with Ari |
| **Right (20%)** | Tools called, memory chunks, model reasoning |

---

## 🛣️ Roadmap

- [x] Session-based chat indexing
- [x] LLM-powered memory rewriting
- [x] FAISS vector storage
- [x] User persona generation
- [x] FastAPI backend with RAG pipeline
- [x] Hybrid search (75% cosine + 25% BM25)
- [x] CrossEncoder re-ranking
- [x] Fusion retrieval with query expansion
- [x] Tool calling integration (get_user_persona, get_long_term_memory)
- [x] Safety guardrails with LlamaGuard 4
- [x] Streamlit 3-pane frontend (prototype)
- [x] **Next.js production frontend at `/chat`**
- [x] **WhatsApp-style message bubbles**
- [x] **Tool use error recovery**
- [ ] Multi-user support
- [ ] Streaming responses
- [ ] Session persistence (database)

---

## 📄 License

This project is for demonstration and learning purposes and not to compete commercially with Rumik.ai. 

---

<p align="center">
  <strong>Built with ❤️ by Akshansh for showcasing long-term AI memory</strong>
</p>
