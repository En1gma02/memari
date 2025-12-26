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

Memari implements a **4-Layer Hybrid Memory System**:

```
┌──────────────────────────────────────────────────────────────────────────┐
│                            MEMORY ARCHITECTUR                            │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────┐  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │  SHORT-TERM  │  │    USER     │  │  LONG-TERM   │  │   ARI'S      │   │
│  │  MEMORY      │  │   PERSONA   │  │   MEMORY     │  │   LIFE       │   │
│  ├──────────────┤  ├─────────────┤  ├──────────────┤  ├──────────────┤   │
│  │ Last  10 msgs│  │ Structured  │  │ FAISS Vector │  │ FAISS Vector │   │
│  │ + session in │  │ MD file     │  │ DB: User     │  │ DB: Ari's    │   │
│  │ context      │  │ with user   │  │ chat history │  │ life story   │   │
│  │ window       │  │ facts       │  │ embeddings   │  │ (334 chunks) │   │
│  └──────────────┘  └─────────────┘  └──────────────┘  └──────────────┘   │
│         ▲                 ▲                  ▲                 ▲         │
│         │                 │                  │                 │         │
│    Always Active     Tool Call          Tool Call         Tool Call      │
│                   get_user_persona  get_long_term_memory get_self_info   │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

### Memory Layers

| Layer | Purpose | Storage | Retrieval |
|-------|---------|---------|-----------|
| **Short-Term** | Immediate conversation context | In-memory buffer | Always included |
| **User Persona** | Facts, preferences, personality | Markdown file | Tool call |
| **Long-Term** | Historical conversations | FAISS + Embeddings | RAG Pipeline |
| **Ari's Life** | Ari's background, experiences, personality | FAISS + Embeddings | RAG Pipeline |

---

## 🔧 Tech Stack

| Component | Technology |
|-----------|------------|
| **Frontend** | Next.js 16 + React 19 + shadcn/ui + Tailwind v4 |
| **Backend** | FastAPI (Python) |
| **Vector DB** | FAISS (faiss-cpu) |
| **Embeddings** | sentence-transformers (`all-MiniLM-L6-v2`) |
| **Re-ranking** | CrossEncoder (`ms-marco-MiniLM-L6-v2`) |
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
│   ├── rag_engine.py      # V2 Hybrid RAG (cosine + BM25, query expansion, reranking, adaptive K)
│   ├── prompts.py         # System prompts & tool definitions
│   ├── config.py          # Configuration & environment
│   ├── models.py          # Pydantic models
│   ├── requirements.txt
│   ├── helper-scripts/
│   │   ├── index_chat.py           # Index chat → FAISS
│   │   ├── index_ari_life.py       # Index Ari's life → FAISS
│   │   ├── chat_to_user_persona.py # Generate persona
│   │   └── index_to_json.py        # Export to JSON
│   ├── data/
│   │   ├── CHAT.txt
│   │   ├── user-persona.md
│   │   ├── ari-life.md             # Ari's life story
│   │   ├── faiss_index.bin         # User chat index
│   │   ├── faiss_index_ari.bin     # Ari's life index
│   │   ├── metadata.pkl
│   │   └── metadata_ari.pkl
├── benchmark/             # RAG benchmark suite
│   ├── rag_benchmark.py           # V1 engine
│   ├── rag_benchmark_v2.py        # V2 optimized engine
│   ├── rag_benchmark_v3.py        # V3 experimental
│   ├── run_benchmark.py           # Benchmark runner
│   ├── metrics.py                 # Retrieval & QA metrics
│   ├── generate_queries.py        # Test query generator
│   ├── benchmarks.md              # Results & findings
│   └── results/                   # CSV & JSON outputs
├── frontend/              # Next.js frontend
├── llm-docs/              # Cerebras & Groq API docs
├── memari-docs/           # Project documentation
├── streamlit/             # Prototype streamlit app
│   ├── app.py
│   └── requirements.txt
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

### Retrieval Flow (V2 Hybrid Search)

```
             User Query
                 ↓
         Query Expansion (LLM adds synonyms)
                 ↓
┌─────────────────────────────────────────────┐
│  FAISS (50 candidates) → BM25 (candidates)  │
│        75% Cosine + 25% BM25                │
└─────────────────────────────────────────────┘
                 ↓
      CrossEncoder Re-ranking (normalized)
                 ↓
         Adaptive Top-K (3/5/7)
                 ↓
Contextual Expansion (±1 neighbors, ≥25% only)
                 ↓
              LLM Context
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
- **V2 RAG Pipeline**: Query expansion + FAISS-first BM25 + Adaptive K + Contextual expansion
- **Parallel Fusion Retrieval**: Low-confidence queries trigger parallel multi-query search using ThreadPoolExecutor
- **Self-Awareness**: Ari has access to her own life story via `get_self_info` tool (334 indexed chunks)
- **Three-View Interface**: Seamlessly switch between Chat History, User Persona, and Ari's Life
- **Smart Safety Layer**: LlamaGuard flags are passed as warnings to the LLM (handles Hinglish false positives)
- **Zero-Shot Prompts**: Optimized prompts following Groq best practices (no example copying)
- **Identity Protection**: Ari never identifies as AI/OpenAI/GPT

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
| **Left (20%)** | Dropdown selector: Chat History, User Persona, or Ari's Life with markdown rendering |
| **Center (60%)** | Main chat interface with Ari |
| **Right (20%)** | Memory Panel: Available tools, tools used, retrieved context chunks |

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
- [x] Tool calling integration (get_user_persona, get_long_term_memory, get_self_info)
- [x] Safety guardrails with LlamaGuard 4
- [x] Streamlit 3-pane frontend (prototype)
- [x] **Next.js production frontend at `/chat`**
- [x] **WhatsApp-style message bubbles**
- [x] **Tool use error recovery**
- [x] **Ari's Life knowledge base (334 indexed chunks)**
- [x] **Custom dropdown selector with view descriptions**
- [x] **Markdown rendering for persona and life story**
- [x] **V2 RAG: Query expansion, FAISS-first BM25, Adaptive K**
- [x] **Contextual chunk expansion (±1 neighbors)**
- [x] **RAG Benchmark Suite (V1/V2/V3 comparison)**
- [x] **Zero-shot prompts (Groq best practices)**
- [x] **Parallel fusion retrieval (ThreadPoolExecutor)**
- [x] **Smart safety layer (warning injection vs blocking)**
- [x] **Identity protection (never identifies as AI)**
- [x] **Proactive tool usage (aggressive memory access)**
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
