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
| **Frontend** | Next.js 15, Tailwind CSS, Shadcn UI |
| **Backend** | FastAPI (Python) |
| **Vector DB** | FAISS (faiss-cpu) |
| **Embeddings** | sentence-transformers (`all-MiniLM-L6-v2`) |
| **LLM - Fast** | Cerebras (`llama-3.1-8b`) |
| **LLM - Smart** | Groq (`gpt-oss-120b` with reasoning) |
| **Safety** | Groq (`llama-guard-4-12b`) |

---

## 📁 Project Structure

```
memari/
├── backend/
│   ├── helper-scripts/
│   │   ├── index_chat.py       # Index chat history → FAISS
│   │   ├── index_to_json.py    # Export index to JSON
│   │   └── chat_index.json     # Viewable indexed chunks
│   ├── main.py                 # FastAPI application
│   ├── ari-system-prompt.md    # Ari's personality prompt
│   ├── ari-life.md             # Ari's persona/backstory
│   ├── faiss_index.bin         # FAISS vector index
│   ├── metadata.pkl            # Index metadata
│   └── requirements.txt
├── frontend/                   # Next.js web app
├── llm-docs/                   # Cerebras & Groq API docs
├── memari-docs/                # Project documentation
├── CHAT.txt                    # Sample chat history (30K tokens)
├── IDEA_CONTEXT.md             # Project vision & architecture
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

### 3. Index Chat History

```bash
cd backend/helper-scripts
python index_chat.py
```

This will:
1. Load `CHAT.txt` and split into sessions
2. Rewrite each session with LLaMA 3.1 8B for optimal retrieval
3. Generate embeddings with `all-MiniLM-L6-v2`
4. Save FAISS index and metadata

### 4. Run Backend

```bash
cd backend
uvicorn main:app --reload
```

### 5. Run Frontend

```bash
cd frontend
bun install
bun dev
```

---

## 🧪 Long-Term Memory Pipeline

### Indexing Flow

```
CHAT.txt → Session Chunking → LLM Rewriting → Embeddings → FAISS Index
              ("Human 1: Hi")   (Cerebras)    (MiniLM)
```

### Retrieval Flow

```
User Query → Query Expansion → Hybrid Search → Reranking → Context Expansion
                (4 queries)    (Dense + BM25)              (neighboring chunks)
                    ↓
            Response Generation ← Safety Check ← LLM Response
                (Groq gpt-oss-120b)  (LlamaGuard)
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
- [ ] FastAPI backend with RAG pipeline
- [ ] Fusion retrieval with query expansion
- [ ] Reranking algorithm
- [ ] Context expansion (neighboring chunks)
- [ ] User persona management
- [ ] Tool calling integration
- [ ] Next.js frontend
- [ ] Safety guardrails with LlamaGuard

---

## 📄 License

This project is for demonstration and learning purposes.

---

<p align="center">
  <strong>Built with ❤️ by Akshansh for showcasing long-term AI memory</strong>
</p>
