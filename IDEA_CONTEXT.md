I want to create a super human like AI chatbot named 'Ari' which is like a clone of Rumik AI's IRA. It will be like talking to a friend on whatsapp. It will be india focussed so conversation style should be like Indian Hinglish and modern tone and language. The novelty being it should have infinitely long memory for a user, just like a human remembers references to events that were discussed years ago.

Honestly speaking i interviewed for rumik and in 1st round we discussed about the memory problem and i want to try solving it and showcasing it to them as a strong point and mail it to them.

Relevant ideas i got from perplexity deep research:
1. Hybrid Memory Architecture (The Gold Standard)
The most effective approach combines three complementary layers rather than relying on a single technique:

Layer 1: Active Working Context (FIFO Buffer)
Keep only the last N turns (~5-10 recent messages) in your context window
These are raw, unprocessed—maximum information density for immediate context
Costs minimal tokens but gives the model "short-term awareness"

Layer 2: Structured Semantic Memory
What to store: Key facts, preferences, relationships, milestones extracted from conversations
"User got promoted to Engineering Lead at TechCorp on March 2024"
"Prefers detailed technical explanations"
"Has anxiety about public speaking"
"Trip to Japan lasted 2 weeks, visited Tokyo and Kyoto"
Storage format: Use a knowledge graph or structured JSON database
Neo4j/Graph databases: Model relationships naturally (User → knows → Person → works_at → Company)
Key-value store: Fast, simple retrieval for facts
Vector embeddings: For semantic similarity ("travel experiences" queries)
Extraction: Use the LLM itself to extract these facts between conversation turns—doesn't need to be real-time

Layer 3: Vector Database for Semantic Retrieval
Index entire conversation history as embeddings
At each new user message, retrieve the top 3-5 most relevant past exchanges using semantic similarity
Costs: ~10-20 tokens but captures nuanced context that structured memory might miss

2. ChatGPT-Style User Memory Management (Product Approach)
OpenAI's approach for their memory feature:
Architecture:
Saved Memories: A structured document (1-2 pages) of facts the user explicitly asks to remember
Automatic Extraction: Background process scans conversations, suggests memories ("Looks like you prefer documentation over videos?")
Per-conversation Prepending: Memory document is always included at prompt start
Why it works:
Simple, interpretable to users
Hybrid: explicit + automatic
Minimal overhead (usually <500 tokens)


Currunt code structure:
├── backend/ (folder: fast api backend will go here)
│   ├── helper-scripts/
│             └──index_chat.py
│   ├── .env
│   ├── ari-life.md  (detailed data for ari's persona and life history)
│   ├── ari-system-prompt.md  (ari's system prompt)
│   ├── .env
│   ├── main.py (fastapi main file)
│   └── requirements.txt
├── frontend/ (folder: nextjs webapp lives here)
│   └── (Nextjs Tailwind Shadcn bun setup using bunx --bun shadcn@latest create --preset "https://ui.shadcn.com/init?base=base&style=nova&baseColor=neutral&theme=emerald&iconLibrary=lucide&font=figtree&menuAccent=subtle&menuColor=default&radius=small&template=next" --template next)
├── llm-docs/ (cerebras and groq documentation, contains: cerebras-batch-api.md, cerebras-prompt-caching.md, cerebras-reasoning.md, cerebras-streaming.md, cerebras-structured-outputs.md, cerebras-tool-calling.md, groq-content-moderation.md, groq-prompt-caching.md, groq-reasoning.md, groq-structured-outputs.md, groq-text-generation.md, groq-tool-use.md)
├── memari-docs/ (our app documentation)
│   ├── backend.md (technical documentation of our backend)
│   ├── design-skill.md (Clause skill for better design development for our coding agent)
│   └── frontend.md (technical documentation of our frontend)
├── .gitignore
├── app.py (streamlit app for initially experimenting and building a robust backend)
├── CHAT.txt (chat history database)
└── README.md

Chat.txt is human chat database i will be using as the long history with Tokens - 30,375 & Characters - 116,156. Each line of the document is from the alternate person. Eg piece from the file:
Human 1: Hi!
Ari: What is your favorite holiday?
Human 1: one where I get to meet lots of different people.
Ari: What was the most number of people you have ever met during a holiday?
Human 1: Hard to keep a count. Maybe 25.
Ari: Which holiday was that?

Screenshot - Rumik ai's ira frontend design. I am inspired by this design but i want other things added as this is for showcasing long term memory. My vision - 
Left 20% pane: the chat history database i have showcased in a good conversation look so one can reference it to test long term memory and ask questions.
Middle 60% pane: the chat interface with AI, i like the ira interface we can clone it
Right 20%: Showing the tools that were called, the chunks from long term memory and the reasoning of the model 

##My architectural solution to solve the memory problem:

###Short term memory:
String of past 5-10 messages when user starts a session and continue to add the ongoing conversation going on as the session progresses.

###About the user:
A structured markdown file specialized about the user with facts the user explicitly asks to remember. And things the user likes and the complete persona/ personalioty of the user. 
Use cerebras's "llama3.1-8b" to keep updating this file after every session. 
Be stict to add only extremely relevent user persona things, we dont want this to grow large or become 'psuedo-memory'

###Long term memory:
Indexing:
Use faiss as our vector db.
A session conversation with Ari decided based on datetime based session, like once user started talking then went away for more than 30mins that is a unique session, is sent to cerebras's "llama3.1-8b" to rewrite it in a way that it is good for storing in memory vector db context for retrieval in future.
If the text is in hinglish or other language, thhe model still outputs the context in english so it is compatible with our MiniLM embedding model.  
The session time stamp is concatenated with the clean data. 
We use batch api for this as it is cost effective and doesnt require instant response.
The response is then gone through a pipeline of overlapped chunking including their actual timestamps
The chunks are indexed using "sentence-transformers/all-MiniLM-L6-v2" and then stored in faiss vector dbbelonging to user.

Retrieval:  
Use cerebras's "llama3.1-8b" Use fusuion retrieval to get good 4 alternative queries
Take those queries, index them using sentence-transformers/all-MiniLM-L6-v2, and permorm hybrid cosine similarity and bm25 to pull back 5 vector db results for each one
Run a reranking algorithm to limit the results down to around 5 'hits'
Next up is taking the hits and expanding it to include neighboring 'chunks' in the chat history
Then format the chunks neatly
Then pass the context and user's prompt to groq's "openai/gpt-oss-120b" with thinking active for it to answer the users question.

Generation:
Then pass the context and user's prompt to groq's "openai/gpt-oss-120b" with thinking active for it to answer the users question.
The query and models response is passed through groq's "meta-llama/llama-guard-4-12b" for safety checks and then the final response is sent to the user.

Latency vs. Complexity
The Bottleneck: Fusion Retrieval (4 queries) + Hybrid Search + Reranking is heavy.
Optimization: Since this is a WhatsApp-style chat, speed is key.
Start with just Dense Retrieval (Vector) + Reranking.
Only trigger "Fusion" (query expansion) if the cosine similarity score of the top result is low (e.g., < 0.7), implying the AI is confused.

##We dont need memory always we use tools
Short term memory is always used during conversation
Use tool calling when we need memory:
get_user_persona - tool which retreives the user persona document and adds that to ari's main response llm for context
get_long_term_memory - tool which retreives the long term memory using our RAG pipeline and adds that to ari's main response llm for context