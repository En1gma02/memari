# Landing Page Documentation

## Overview

The Memari landing page (`/`) is designed as an **Engineering HUD** (Heads-Up Display) targeting technical audiences (CTOs, interviewers). It showcases the system's architecture through a dense, data-rich interface inspired by system monitors and IDE debuggers.

**Route**: `frontend/app/page.tsx`

---

## Design Philosophy

| Aspect | Approach |
|--------|----------|
| **Target Audience** | CTOs, Technical Interviewers |
| **Aesthetic** | "Sci-Fi Server Dashboard" / "System Monitor" |
| **Color Palette** | Deep black (`#0A0A0A`), Card surfaces (`#111111`), Emerald accents (`#10b981`) |
| **Typography** | `Geist Mono` for all technical labels and data |
| **Icons** | `lucide-react` vectors only (no emojis) |

---

## Layout Structure

The page uses a **3-column grid layout** (approximately 22% | 56% | 22%):

```
┌────────────────────────────────────────────────────────────────┐
│                        ENGINEERING HUD                          │
├─────────────┬──────────────────────────────┬───────────────────┤
│   LEFT      │          CENTER              │      RIGHT        │
│   (22%)     │          (56%)               │      (22%)        │
├─────────────┼──────────────────────────────┼───────────────────┤
│ Hero Card   │                              │  Benchmark Stats  │
│ - MEMARI    │   Pipeline Architecture      │  - Hit Rate: 88%  │
│ - v2.1.0    │   (Tabbed: Index/Infer)      │  - 100 Queries    │
│ - CTA       │                              │                   │
├─────────────┤                              ├───────────────────┤
│ Data Schema │                              │   Tech Stack      │
│ - 4 Layers  │                              │   - Badge Pills   │
│ - Stats     │                              │                   │
└─────────────┴──────────────────────────────┴───────────────────┘
```

---

## Components

### 1. Hero Section (`hero-section.tsx`)

**Purpose**: Branding and primary CTA

| Element | Content |
|---------|---------|
| Version Badge | `v2.1.0-beta` with pulsing emerald dot |
| Title | `MEMARI` (all caps) |
| Subtitle | "Tool Calling based Hybrid RAG architecture for Long-Term Persistent memory" |
| CTA Button | Solid emerald, `>_ .start-demo.sh` with animated cursor |

**Styling**: 
- `justify-between` layout for vertical distribution
- `p-4` padding, `space-y-4` gaps

---

### 2. Data Schema (`memory-layers.tsx`)

**Purpose**: Showcase the 4-layer memory architecture

| Layer | File | Key Stat |
|-------|------|----------|
| Short Term Memory | `short_term.buffer` | 10 msgs + session |
| Long Term Chat History | `chat_history.bin` | 93 sessions, 29,645 tokens |
| Learned User Persona | `user_persona.md` | 2,450 tokens |
| Ari's Life | `ari_life.bin` | 334 chunks, 138,908 tokens |

**Styling**:
- Monochrome (purple header icon, emerald value accents)
- Technical file extension notation (`.bin`, `.md`, `.buffer`)
- Grid background overlay

---

### 3. Pipeline Architecture (`pipeline-architecture.tsx`)

**Purpose**: Visualize the dual data flows (Indexing & Inference)

**Tabs**:
1. **Indexing (Write Path)**:
   - Input Source (`CHAT.txt`)
   - Session Split (Regex)
   - Rewriting (Cerebras LLaMA 3.1)
   - Embedding (MiniLM-L6-v2)
   - Vector DB (FAISS + BM25)

2. **Inference (Read Path)**:
   - User Input
   - Safety Check (LlamaGuard 4)
   - Query Expansion (Groq LLaMA)
   - Hybrid RAG (FAISS + CrossEncoder)
   - Generation (Groq LLaMA 70B)

**Visuals**:
- "Chip" node design with header/footer
- Animated progress line
- Latency metrics per node
- Corner bracket decorators on active nodes

---

### 4. Benchmark Stats (`benchmark-stats.tsx`)

**Purpose**: Display retrieval performance metrics

| Metric | Value |
|--------|-------|
| Retrieval Hit Rate | 88% (circular SVG ring) |
| Benchmark Scale | "100 Queries tested over 65 Million Tokens database" |

---

### 5. Tech Badges (`tech-badges.tsx`)

**Purpose**: Showcase the technology stack

| Technology | Icon Color |
|------------|------------|
| Cerebras | Orange |
| Groq | Red |
| FastAPI | Emerald |
| Next.js | White |
| FAISS | Blue |
| LangChain | Yellow |

**Styling**: Pill badges with icon + text

---

## Global Styling

### CSS Variables (Dark Theme)

```css
.dark {
  --background: #0A0A0A;
  --card: #111111;
  --primary: #10B981; /* Emerald 500 */
  --border: rgba(255, 255, 255, 0.1);
}
```

### Animations

- **flowDash**: Animated dashed lines for pipeline connections
- **pulse**: Status indicators and cursor blinks

---

## Future Improvements

- [ ] Mobile responsiveness (currently optimized for desktop)
- [ ] Interactive pipeline node clicks (show details modal)
- [ ] Real-time stats from backend API
- [ ] Add "Comparison" chart (Memari vs Standard RAG)

---

## File Structure

```
frontend/
├── app/
│   └── page.tsx                    # Main layout orchestrator
├── components/
│   └── landing/
│       ├── hero-section.tsx        # Branding + CTA
│       ├── memory-layers.tsx       # Data Schema (4 layers)
│       ├── pipeline-architecture.tsx # Tabbed flow viz
│       ├── benchmark-stats.tsx     # Performance metrics
│       └── tech-badges.tsx         # Stack pills
```
