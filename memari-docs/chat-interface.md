# Chat Interface Documentation

## Overview
The `/chat` route provides a fully-featured WhatsApp-style chat interface for interacting with Ari, the AI chatbot.

## Architecture

### Three-Panel Layout
The chat interface uses a fixed three-column grid layout with independent scrolling:
- **Left Panel (280px)**: History/Persona viewer
- **Center Panel (flex-1)**: Main chat interface  
- **Right Panel (280px)**: Memory panel

All panels have uniform 72px headers and footers for visual consistency.

## Left Panel: History/Persona/Life Viewer

### Features
- **Custom Dropdown Selector**: Sleek select component with three views
  - Clean title-only trigger (icon + text)
  - Dropdown items include secondary descriptive text
  - Description text shown below dropdown updates based on selection
  
### View Options

#### 1. Chat History View
- **Description**: "Chat database used for long term memory. Updated after every chat session."
- Displays `backend/data/CHAT.txt` as chat bubbles
- Parses "Human X:" and "Ari:" message format
- Auto-sized bubbles with proper alignment
- Shows up to 150 messages (with count for overflow)
- **Footer Stats**: 93 Sessions, 750 Messages, 29,645 Tokens, 13,255 Embedded

#### 2. User Persona View
- **Description**: "User's stored preferences, personality traits, and facts. Updated after every session. Fully Passed when get_user_persona tool is called."
- Renders `backend/data/user-persona.md` as formatted markdown
- Supports headers (# ##), lists, bold text, horizontal rules
- Clean card design with border and padding
- **Footer Stats**: 2,450 Tokens, 15,800 Characters

#### 3. Ari's Life View ✨ NEW
- **Description**: "Information about Ari's life. Undergoes RAG pipeline when 'get_self_info' tool is called."
- Renders `backend/data/ari-life.md` using react-markdown
- Full markdown support: headings, paragraphs, lists, horizontal rules, blockquotes, bold
- Custom styled with proper typography hierarchy
- **Footer Stats**: 334 Chunks, 138,908 Tokens

### Dynamic Footer
- Displays view-specific statistics (left-aligned)
- Font sizes: `text-xs` for numbers, `text-[8px]` for labels
- Updates automatically based on selected view

## Center Panel: Chat Interface

### Header (72px)
- **Profile Picture**: 48x48px circle with ring, proper cropping
- **Name & Status**: "Ari" with "Online"/"Offline" indicator
- **Online Indicator**: Green (online) / Grey (offline) dot
- **Action Icons**: 
  - GitHub link (`github` icon) → https://github.com/En1gma02/memari
  - Clear chat (`eraser` icon) → Resets session

### Message Display
- **Auto-scroll** to bottom on new messages
- **Date separators**: "Today", "Yesterday", or full date
- **Message grouping**: Items-end for user, items-start for assistant
- **Typing indicator**: Animated bouncing dots when loading

### Message Bubbles
- **Auto-sized**: `max-w-[75%]` with `w-fit`
- **User bubbles**: Emerald background (`bg-primary`), rounded-br-sm
- **Assistant bubbles**: Card background with border, rounded-bl-sm
- **Timestamps**: HH:MM format (24-hour)
- **Status indicators** (user messages only):
  - ✓ (Check) - White/80 opacity = Sent
  - ✓✓ (CheckCheck) - Dark navy (#1e3a5f) = Delivered

### Input Area (72px)
- **Textarea**: Auto-resizing (max 120px height)
- **Keyboard shortcuts**:
  - `Enter` → Send message
  - `Shift + Enter` → New line
- **Send button**: 44x44px with Send icon
- **Helper text**: "Press Enter to send, Shift+Enter for new line"

### Empty State
- Centered vertically with `h-full min-h-[60vh]`
- Profile picture (80x80px)
- Welcome heading: "Start a conversation"
- Helper text about personalized responses

## Right Panel: Memory Panel

### Header
- Title: "Memory Panel" (renamed from "Debug Panel")
- Session ID displayed in small mono font

### Available Tools Section
- Shows all tools available to the LLM
- Each tool displayed with:
  - Icon in colored box (User, Search, BookOpen)
  - Tool name in mono font
  - Description text (11px)
- Tools:
  - `get_user_persona` - "Retrieves user's stored preferences, personality traits, and facts"
  - `get_long_term_memory` - "Semantic search through indexed conversation history using hybrid RAG"
  - `get_self_info` ✨ NEW - "Retrieves information about Ari's life story, background, and personality"

### Tools Used Section
- Green-themed display for active tool calls
- Shows which tools were actually invoked
- Empty state: "No tools called yet"

### Retrieved Context Section
- Multiple expandable dropdowns (one per chunk)
- Each shows: "Chunk X (Score%)" 
- Click to expand full text in mono font
- Empty state: "No context retrieved"

### Footer (72px)
Technical pipeline information (10px font):
- **Rephrased Fusion Retrieval** (foreground/70)
- **Hybrid RAG: 75% Cosine + 25% BM25**
- **CrossEncoder Re-ranking** (primary color)

## State Management

### Message Status Flow
1. **User sends message**:
   - Status: `sending` (grey Check icon)
   - Message added to state with timestamp
2. **After 300ms**:
   - Status: `sent` (white Check icon)
3. **Backend responds**:
   - Status: `delivered` (blue CheckCheck icon)
   - Assistant messages added

### Data Loading
- **Chat History**: Fetched from `/api/data?file=CHAT.txt`
- **User Persona**: Fetched from `/api/data?file=user-persona.md`
- **Health Check**: Polled every 30 seconds
- **Context Parsing**: Extracts numbered chunks with regex pattern

## API Integration

### Endpoints Used
- `POST /chat` - Send messages (with retry logic)
- `GET /health` - Backend health check
- `GET /api/data` - Fetch local data files

### Error Handling
- **Retry Logic**: Up to 2 retries with exponential backoff (500ms, 1000ms)
- **Backend Errors**: Gracefully handled, shows user-friendly message
- **Offline Detection**: Shows "Backend Unavailable" screen with retry option
- **Tool Use Failures**: Backend extracts valid responses from failed_generation

### Context Chunk Parsing
Parses two formats:
1. **Numbered format**: `1. (Score: 0.482)\nText...`
2. **Separator format**: Split by `\n\n---\n\n`

## Styling

### Colors
- **Primary**: Emerald (#10b981)
- **Background**: Dark theme by default
- **Glassmorphism**: `bg-card/30 backdrop-blur-sm`
- **Borders**: `border-border/50` for subtle separation

### Typography
- **Headers**: Figtree font family
- **Code/Mono**: Geist Mono for session IDs, tool names
- **Sizes**: Carefully balanced from 8px to 20px

### Layout
- **Fixed height**: `h-screen` prevents page scroll
- **Independent scroll**: Each panel uses `ScrollArea` component
- **Overflow handling**: `min-h-0` on flex children

## Components

### File Structure
```
components/chat/
├── chat-interface.tsx       # Main chat UI
├── message-bubble.tsx       # Message bubbles + typing + date
├── chat-history.tsx         # Left panel with dropdown selector
├── debug-panel.tsx          # Right panel (Memory Panel)
└── index.ts                 # Barrel exports

lib/
├── api.ts                   # Backend API client
└── data.ts                  # Data fetching (history, persona, ari-life)

app/
├── chat/
│   └── page.tsx             # Main chat page
└── api/
    ├── data/
    │   └── route.ts         # Data file API route
    └── ari-life/
        └── route.ts         # Ari's life content API route ✨ NEW
```

## Design Principles

### WhatsApp-Inspired
- Familiar chat bubble design
- Status indicators (ticks)
- Timestamps on messages
- Profile header with status

### Premium Aesthetics
- Glassmorphism effects
- Smooth animations (fade-in, slide-in)
- Micro-interactions (hover states)
- Consistent spacing and alignment

### Accessibility
- Tooltips on interactive elements
- Clear visual hierarchy
- High contrast text
- Keyboard navigation support
