"""
index_chat.py - Chat History Indexer for Memari's Long-Term Memory System

This script processes a raw text chat history (CHAT.txt):
1. Chunks it into sessions based on the delimiter "Human 1: Hi"
2. Rewrites each session using Cerebras LLaMA 3.1 8B for optimal retrieval
3. Generates embeddings using sentence-transformers
4. Saves a FAISS index for efficient semantic retrieval

Usage: Run from backend/helper-scripts/ directory
    python index_chat.py

Output:
    - backend/faiss_index.bin: FAISS index file
    - backend/metadata.pkl: Pickle file mapping index IDs to text content
"""

import os
import sys
import pickle
import time
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from cerebras.cloud.sdk import Cerebras
from dotenv import load_dotenv


# ==============================================================================
# CONFIGURATION
# ==============================================================================

# Load environment variables from backend/.env
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(SCRIPT_DIR, "..", ".env")
load_dotenv(ENV_PATH)

# Paths (relative to script location: backend/helper-scripts/)
CHAT_FILE_PATH = os.path.join(SCRIPT_DIR, "..", "..", "CHAT.txt")
FAISS_INDEX_PATH = os.path.join(SCRIPT_DIR, "..", "faiss_index.bin")
METADATA_PATH = os.path.join(SCRIPT_DIR, "..", "metadata.pkl")

# Model configuration
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
EMBEDDING_DIMENSION = 384  # Dimension for all-MiniLM-L6-v2
CEREBRAS_MODEL = "llama-3.1-8b"

# Rate limiting: Cerebras has 30 requests/minute limit
# We add 2 seconds delay between API calls to stay well under the limit
API_DELAY_SECONDS = 2

# Session delimiter - A new session starts when this exact phrase appears
SESSION_DELIMITER = "Human 1: Hi"


# ==============================================================================
# PROMPTS FOR MEMORY CONVERSION
# ==============================================================================

# System prompt that instructs the LLM how to convert chat to memory format
MEMORY_SYSTEM_PROMPT = """You are a Memory Conversion Specialist for an AI chatbot's long-term memory system.

Your task is to transform raw conversation sessions into optimized memory entries that will be stored in a vector database for future semantic retrieval.

## Conversion Guidelines:

1. **Extract Key Information**: Identify and preserve important facts, events, preferences, emotions, and commitments mentioned in the conversation.

2. **Semantic Clarity**: Rewrite content in clear, descriptive English sentences that will match well with future search queries. Even if original is in Hinglish or other language, output must be in English.

3. **Context Preservation**: Include relevant context so the memory makes sense standalone without needing the full conversation.

4. **Temporal Markers**: Preserve any time references (dates, days, "yesterday", "next week") and convert relative times to descriptive phrases.

5. **Entity Extraction**: Clearly mention names of people, places, events, and things discussed.

6. **Emotional Context**: Note the emotional tone or significant feelings expressed during the conversation.

7. **Actionable Items**: Highlight any commitments, plans, or action items discussed.

## Output Format:
- Write in third person perspective about "the user" and "Ari"
- Use clear, searchable sentences
- Keep the output concise but information-rich
- Do NOT include any preamble or explanation, just output the memory text directly

## Example:
Input: "Human 1: Hi!\nAri: Hey! How was your weekend?\nHuman 1: It was great! Went to Goa with college friends.\nAri: Nice! Which beach did you visit?\nHuman 1: Baga beach, it was crowded but fun."

Output:
The user went on a weekend trip to Goa with their college friends. They visited Baga beach and found it crowded but enjoyable. The user had a great time during this trip."""


def create_memory_prompt(session_text: str) -> str:
    """
    Create the prompt for converting a chat session to memory format.
    
    Args:
        session_text: Raw conversation session text
        
    Returns:
        Formatted prompt for the LLM
    """
    return f"""Convert the following conversation session into an optimized memory entry for vector database storage:

---CONVERSATION START---
{session_text}
---CONVERSATION END---

Memory Entry:"""


# ==============================================================================
# FUNCTIONS
# ==============================================================================

def load_and_chunk_chat(file_path: str) -> list[str]:
    """
    Load the chat file and split it into session chunks.
    
    Splitting Logic:
    - Read all lines from the file
    - When "Human 1: Hi" is encountered, save accumulated lines as a session
    - Start accumulating new lines for the next session
    - At the end, save any remaining accumulated lines as the final session
    
    Args:
        file_path: Path to the CHAT.txt file
        
    Returns:
        List of session chunks (strings)
    """
    print(f"[1/5] Loading chat file: {file_path}")
    
    if not os.path.exists(file_path):
        print(f"ERROR: Chat file not found at {file_path}")
        sys.exit(1)
    
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    lines = content.split("\n")
    print(f"      Total lines in file: {len(lines)}")
    
    # Split into sessions based on the delimiter "Human 1: Hi"
    # =========================================================================
    # SPLITTING LOGIC EXPLANATION:
    # The chat history is split into "sessions" using "Human 1: Hi" as delimiter.
    # Every occurrence of "Human 1: Hi" marks the START of a new conversational
    # session. Previous accumulated lines become one session chunk.
    # 
    # Example:
    #   Line 1: Human 1: Hi           <- Start of Session 1
    #   Line 2: Ari: Hello!
    #   Line 3: Human 1: How are you?
    #   Line 4: Ari: I'm good!
    #   Line 5: Human 1: Hi           <- Start of Session 2
    #   ...
    # =========================================================================
    sessions = []
    current_session_lines = []
    
    for line in lines:
        stripped_line = line.strip()
        
        # Skip empty lines for cleaner chunks
        if not stripped_line:
            continue
        
        # Check if this line is a session delimiter
        if stripped_line.startswith(SESSION_DELIMITER):
            # If we have accumulated lines, save them as a completed session
            if current_session_lines:
                session_text = "\n".join(current_session_lines)
                sessions.append(session_text)
            
            # Start a new session with this greeting line
            current_session_lines = [stripped_line]
        else:
            # Add line to current session
            current_session_lines.append(stripped_line)
    
    # Don't forget the last session (no trailing delimiter)
    if current_session_lines:
        session_text = "\n".join(current_session_lines)
        sessions.append(session_text)
    
    print(f"      Sessions found: {len(sessions)}")
    
    # Log a preview of session sizes
    if sessions:
        avg_lines = sum(len(s.split("\n")) for s in sessions) / len(sessions)
        print(f"      Average lines per session: {avg_lines:.1f}")
    
    return sessions


def rewrite_sessions_with_llm(
    sessions: list[str],
    client: Cerebras
) -> tuple[list[str], list[str]]:
    """
    Use Cerebras LLaMA 3.1 8B to rewrite each session for optimal retrieval.
    
    This step converts raw conversational text into clean, searchable memory
    entries that will embed well and match semantic queries effectively.
    
    Args:
        sessions: List of raw session text chunks
        client: Cerebras API client
        
    Returns:
        Tuple of (rewritten_sessions, original_sessions)
    """
    print(f"\n[2/5] Rewriting sessions with LLaMA 3.1 8B for optimal retrieval...")
    print(f"      Rate limit: {API_DELAY_SECONDS}s delay between API calls")
    print(f"      Estimated time: ~{len(sessions) * API_DELAY_SECONDS / 60:.1f} minutes")
    
    rewritten_sessions = []
    failed_indices = []
    
    for i, session in enumerate(sessions):
        try:
            # Create the prompt for memory conversion
            user_prompt = create_memory_prompt(session)
            
            # Call Cerebras API (non-streaming for simplicity)
            response = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": MEMORY_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                model=CEREBRAS_MODEL,
                max_tokens=512,
                temperature=0.3,  # Lower temperature for consistent output
            )
            
            # Extract the rewritten memory text
            rewritten_text = response.choices[0].message.content.strip()
            rewritten_sessions.append(rewritten_text)
            
            # Progress indicator
            print(f"      [{i + 1}/{len(sessions)}] Session rewritten ({len(rewritten_text)} chars)")
            
        except Exception as e:
            print(f"      [{i + 1}/{len(sessions)}] ERROR: {str(e)[:50]}... Using original")
            # Fallback to original session text if API fails
            rewritten_sessions.append(session)
            failed_indices.append(i)
        
        # Rate limiting: wait between API calls
        # Cerebras has 30 req/min limit, so 2s delay = max 30 req/min
        if i < len(sessions) - 1:  # Don't wait after the last one
            time.sleep(API_DELAY_SECONDS)
    
    # Summary
    success_count = len(sessions) - len(failed_indices)
    print(f"\n      Rewriting complete!")
    print(f"      Successful: {success_count}/{len(sessions)}")
    if failed_indices:
        print(f"      Failed (used original): {failed_indices}")
    
    return rewritten_sessions, sessions


def generate_embeddings(sessions: list[str], model: SentenceTransformer) -> np.ndarray:
    """
    Generate embeddings for each session chunk.
    
    Args:
        sessions: List of session text chunks (rewritten)
        model: Loaded SentenceTransformer model
        
    Returns:
        NumPy array of embeddings with shape (num_sessions, embedding_dim)
    """
    print(f"\n[3/5] Generating embeddings for {len(sessions)} sessions...")
    
    embeddings = []
    batch_size = 32  # Process in batches for efficiency
    
    for i in range(0, len(sessions), batch_size):
        batch = sessions[i:i + batch_size]
        batch_embeddings = model.encode(batch, show_progress_bar=False)
        embeddings.extend(batch_embeddings)
        
        # Progress indicator
        progress = min(i + batch_size, len(sessions))
        print(f"      Progress: {progress}/{len(sessions)} sessions embedded")
    
    embeddings_array = np.array(embeddings).astype("float32")
    print(f"      Embeddings shape: {embeddings_array.shape}")
    
    return embeddings_array


def create_faiss_index(embeddings: np.ndarray) -> faiss.IndexFlatL2:
    """
    Create a FAISS index and add the embeddings.
    
    Uses FlatL2 (L2/Euclidean distance) for exact nearest neighbor search.
    
    Args:
        embeddings: NumPy array of embeddings
        
    Returns:
        FAISS index with embeddings added
    """
    print(f"\n[4/5] Creating FAISS index...")
    
    dimension = embeddings.shape[1]
    
    # Create a FlatL2 index (exact search using L2 distance)
    index = faiss.IndexFlatL2(dimension)
    
    # Add embeddings to the index
    index.add(embeddings)
    
    print(f"      Index created with {index.ntotal} vectors")
    print(f"      Vector dimension: {dimension}")
    
    return index


def save_index_and_metadata(
    index: faiss.IndexFlatL2,
    rewritten_sessions: list[str],
    original_sessions: list[str],
    index_path: str,
    metadata_path: str
) -> None:
    """
    Save the FAISS index and metadata to disk.
    
    The metadata file stores:
    - id_to_text: Mapping of index ID -> rewritten session text (for display)
    - id_to_original: Mapping of index ID -> original session text (for context)
    - Model and configuration info
    
    Args:
        index: FAISS index to save
        rewritten_sessions: List of LLM-rewritten session texts
        original_sessions: List of original session texts
        index_path: Path to save FAISS index
        metadata_path: Path to save metadata pickle file
    """
    print(f"\n[5/5] Saving index and metadata...")
    
    # Create parent directories if they don't exist
    os.makedirs(os.path.dirname(index_path), exist_ok=True)
    os.makedirs(os.path.dirname(metadata_path), exist_ok=True)
    
    # Save FAISS index
    faiss.write_index(index, index_path)
    print(f"      FAISS index saved to: {index_path}")
    
    # Create comprehensive metadata
    metadata = {
        # Rewritten sessions (used for embedding and retrieval display)
        "id_to_text": {i: text for i, text in enumerate(rewritten_sessions)},
        # Original sessions (preserved for full context if needed)
        "id_to_original": {i: text for i, text in enumerate(original_sessions)},
        # Configuration info
        "total_sessions": len(rewritten_sessions),
        "embedding_model": EMBEDDING_MODEL,
        "embedding_dimension": EMBEDDING_DIMENSION,
        "rewrite_model": CEREBRAS_MODEL,
    }
    
    with open(metadata_path, "wb") as f:
        pickle.dump(metadata, f)
    print(f"      Metadata saved to: {metadata_path}")
    
    # Print file sizes
    index_size = os.path.getsize(index_path) / 1024  # KB
    metadata_size = os.path.getsize(metadata_path) / 1024  # KB
    print(f"      Index file size: {index_size:.2f} KB")
    print(f"      Metadata file size: {metadata_size:.2f} KB")


def main():
    """Main execution flow for the chat indexer."""
    print("=" * 70)
    print("  MEMARI - Chat History Indexer")
    print("  Building FAISS index for long-term memory retrieval")
    print("  Using Cerebras LLaMA 3.1 8B for memory optimization")
    print("=" * 70)
    print()
    
    # Validate API key
    api_key = os.environ.get("CEREBRAS_API_KEY")
    if not api_key:
        print("ERROR: CEREBRAS_API_KEY not found in environment!")
        print("       Make sure backend/.env contains CEREBRAS_API_KEY")
        sys.exit(1)
    print("[*] Cerebras API key loaded from .env")
    
    # Initialize Cerebras client
    client = Cerebras(api_key=api_key)
    print("[*] Cerebras client initialized")
    
    # Step 1: Load and chunk the chat file
    sessions = load_and_chunk_chat(CHAT_FILE_PATH)
    
    if not sessions:
        print("ERROR: No sessions found in chat file!")
        sys.exit(1)
    
    # Step 2: Rewrite sessions using LLM for optimal retrieval
    rewritten_sessions, original_sessions = rewrite_sessions_with_llm(sessions, client)
    
    # Step 3: Load embedding model
    print(f"\n[*] Loading embedding model: {EMBEDDING_MODEL}")
    model = SentenceTransformer(EMBEDDING_MODEL)
    print(f"    Model loaded successfully!")
    
    # Step 4: Generate embeddings (on rewritten sessions)
    embeddings = generate_embeddings(rewritten_sessions, model)
    
    # Step 5: Create FAISS index
    index = create_faiss_index(embeddings)
    
    # Step 6: Save everything
    save_index_and_metadata(
        index, 
        rewritten_sessions, 
        original_sessions,
        FAISS_INDEX_PATH, 
        METADATA_PATH
    )
    
    # Success summary
    print()
    print("=" * 70)
    print("  SUCCESS! Chat history indexed successfully.")
    print("=" * 70)
    print(f"  Sessions indexed: {len(rewritten_sessions)}")
    print(f"  Rewrite model: {CEREBRAS_MODEL}")
    print(f"  Embedding model: {EMBEDDING_MODEL}")
    print(f"  FAISS index: {os.path.abspath(FAISS_INDEX_PATH)}")
    print(f"  Metadata: {os.path.abspath(METADATA_PATH)}")
    print()
    print("  Metadata contains both rewritten and original session texts!")
    print("  You can now use these files for semantic retrieval!")
    print("=" * 70)


if __name__ == "__main__":
    main()
