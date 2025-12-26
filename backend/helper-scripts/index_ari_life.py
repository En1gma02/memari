"""
index_ari_life.py - Index Ari's Life Story for RAG

This script processes backend/data/ari-life.md:
1. Chunks content based on sections and token limits (512 tokens max, 50 overlap).
2. Generates embeddings using sentence-transformers.
3. Saves a FAISS index (faiss_index_ari.bin).
4. Saves metadata (metadata_ari.pkl).
5. Exports a readable JSON index (ari_index.json).

Usage: Run from backend/helper-scripts/ directory
    python index_ari_life.py
"""

import os
import sys
import re
import json
import pickle
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Tuple

# ==============================================================================
# CONFIGURATION
# ==============================================================================

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ARI_LIFE_PATH = os.path.join(SCRIPT_DIR, "..", "data", "ari-life.md")
FAISS_INDEX_PATH = os.path.join(SCRIPT_DIR, "..", "data", "faiss_index_ari.bin")
METADATA_PATH = os.path.join(SCRIPT_DIR, "..", "data", "metadata_ari.pkl")
JSON_OUTPUT_PATH = os.path.join(SCRIPT_DIR, "..", "data", "ari_index.json")

# Model configuration
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIMENSION = 384

# Chunking configuration
MAX_TOKENS = 512
OVERLAP_TOKENS = 50
MIN_CHUNK_TOKENS = 200  # Merge if smaller than this
CHARS_PER_TOKEN = 4  # Approximation

# ==============================================================================
# FUNCTIONS
# ==============================================================================

def estimate_tokens(text: str) -> int:
    """Estimate token count based on characters."""
    return len(text) // CHARS_PER_TOKEN

def load_file(file_path: str) -> str:
    """Load the markdown file content."""
    print(f"[1/5] Loading file: {file_path}")
    if not os.path.exists(file_path):
        print(f"ERROR: File not found at {file_path}")
        sys.exit(1)
    
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()

def split_by_headings(text: str) -> List[str]:
    """Split text by markdown headings or horizontal rules."""
    lines = text.split('\n')
    sections = []
    current_section = []
    
    for line in lines:
        if line.strip().startswith(('# ', '## ', '---')):
            if current_section:
                sections.append('\n'.join(current_section))
            current_section = [line]
        else:
            current_section.append(line)
            
    if current_section:
        sections.append('\n'.join(current_section))
        
    return sections

def chunk_text(text: str) -> List[str]:
    """
    Chunk text with sliding window logic.
    """
    # First, respect semantic boundaries (headings)
    raw_sections = split_by_headings(text)
    
    final_chunks = []
    current_buffer = ""
    
    for section in raw_sections:
        section = section.strip()
        if not section:
            continue
            
        # Filter out 0-token sections immediately
        if estimate_tokens(section) <= 0:
            continue
            
        # If section is small enough, try to append to previous buffer if it exists
        section_tokens = estimate_tokens(section)
        
        if section_tokens < MIN_CHUNK_TOKENS:
            # It's a small section
            if current_buffer:
                # Check if adding it to current buffer exceeds max
                if estimate_tokens(current_buffer) + section_tokens < MAX_TOKENS:
                    current_buffer += "\n\n" + section
                    continue
                else:
                    # Current buffer is full, flush it and start new with this small section
                    final_chunks.append(current_buffer)
                    current_buffer = section
            else:
                current_buffer = section
        else:
            # It's a large section or standalone
            # First, flush current buffer if any
            if current_buffer:
                final_chunks.append(current_buffer)
                current_buffer = ""
            
            # If section itself is larger than MAX_TOKENS, split it
            if section_tokens > MAX_TOKENS:
                # Split large section
                max_chars = MAX_TOKENS * CHARS_PER_TOKEN
                overlap_chars = OVERLAP_TOKENS * CHARS_PER_TOKEN
                step_chars = max_chars - overlap_chars
                
                for i in range(0, len(section), step_chars):
                    chunk = section[i : i + max_chars]
                    # Ensure we don't cut words in half ideally
                    if i + max_chars < len(section):
                        last_space = chunk.rfind(' ')
                        if last_space != -1:
                            chunk = chunk[:last_space]
                    
                    if estimate_tokens(chunk) > 0:
                        final_chunks.append(chunk)
            else:
                # Section fits in one chunk
                final_chunks.append(section)
                
    # Flush remaining buffer
    if current_buffer and estimate_tokens(current_buffer) > 0:
        final_chunks.append(current_buffer)
    
    # STRICT FILTER: Discard any chunks with 0 tokens
    filtered_chunks = [c for c in final_chunks if estimate_tokens(c) > 0]
        
    return filtered_chunks

def merge_small_chunks(chunks: List[str]) -> List[str]:
    """
    Double check pass: Merge small chunks (under MIN_CHUNK_TOKENS) with their neighbors.
    This ensures we don't have fragmented small responses.
    """
    if not chunks:
        return []
        
    merged = []
    # Start with the first chunk
    current_chunk = chunks[0]
    
    for i in range(1, len(chunks)):
        next_chunk = chunks[i]
        
        current_tokens = estimate_tokens(current_chunk)
        next_tokens = estimate_tokens(next_chunk)
        
        # If current chunk is small, try to merge forward
        # OR if next chunk is small, try to merge backward
        # Priority: Keep valid chunks within MAX_TOKENS
        
        if (current_tokens < MIN_CHUNK_TOKENS or next_tokens < MIN_CHUNK_TOKENS) and \
           (current_tokens + next_tokens < MAX_TOKENS):
            # Merge
            current_chunk += "\n\n" + next_chunk
        else:
            # Cannot merge, push current and reset
            merged.append(current_chunk)
            current_chunk = next_chunk
            
    # Push the last chunk
    merged.append(current_chunk)
    
    return merged

def generate_embeddings(chunks: List[str], model: SentenceTransformer) -> np.ndarray:
    """Generate embeddings for chunks."""
    print(f"\n[3/5] Generating embeddings for {len(chunks)} chunks...")
    embeddings = model.encode(chunks, show_progress_bar=True)
    return np.array(embeddings).astype("float32")

def create_faiss_index(embeddings: np.ndarray) -> faiss.IndexFlatL2:
    """Create FAISS index."""
    print(f"\n[4/5] Creating FAISS index...")
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings)
    print(f"      Index created with {index.ntotal} vectors")
    return index

def save_artifacts(index, chunks, index_path, metadata_path, json_path):
    """Save index, metadata, and JSON."""
    print(f"\n[5/5] Saving artifacts...")
    
    # Calculate stats
    total_chunks = len(chunks)
    total_chars = sum(len(c) for c in chunks)
    total_tokens = sum(estimate_tokens(c) for c in chunks)
    avg_chars = round(total_chars / total_chunks, 2) if total_chunks else 0
    avg_tokens = round(total_tokens / total_chunks, 2) if total_chunks else 0
    
    print(f"      Stats: {total_chunks} chunks, {total_tokens} tokens total")
    print(f"      Avg: {avg_chars} chars/chunk, {avg_tokens} tokens/chunk")
    
    # Ensure dirs exist
    os.makedirs(os.path.dirname(index_path), exist_ok=True)
    
    # 1. Save FAISS
    faiss.write_index(index, index_path)
    print(f"      FAISS index saved: {index_path}")
    
    # 2. Save Metadata
    metadata = {
        "id_to_text": {i: text for i, text in enumerate(chunks)},
        "id_to_original": {i: text for i, text in enumerate(chunks)},
        "total_sessions": len(chunks),
        "embedding_model": EMBEDDING_MODEL,
        "source": "ari-life.md"
    }
    
    with open(metadata_path, "wb") as f:
        pickle.dump(metadata, f)
    print(f"      Metadata saved: {metadata_path}")
    
    # 3. Save JSON
    json_data = {
        "metadata": {
            "total_chunks": total_chunks,
            "total_chars": total_chars,
            "total_tokens": total_tokens,
            "avg_chars_per_chunk": avg_chars,
            "avg_tokens_per_chunk": avg_tokens,
            "embedding_model": EMBEDDING_MODEL,
            "source": "ari-life.md"
        },
        "chunks": [
            {
                "id": i,
                "text": text,
                "tokens": estimate_tokens(text)
            }
            for i, text in enumerate(chunks)
        ]
    }
    
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(json_data, f, indent=2)
    print(f"      JSON export saved: {json_path}")

def main():
    print("=" * 70)
    print("  MEMARI - Ari Life Indexer")
    print("=" * 70)

    # 1. Load content
    content = load_file(ARI_LIFE_PATH)
    
    # 2. Chunk content
    print(f"\n[2/5] Chunking content (Max: {MAX_TOKENS} tokens, Overlap: {OVERLAP_TOKENS})...")
    chunks = chunk_text(content)
    print(f"      Generated {len(chunks)} raw chunks. Merging small ones...")
    
    # Double check merge
    chunks = merge_small_chunks(chunks)
    
    # One last filter pass just in case merge resulted in empty (unlikely but safe)
    chunks = [c for c in chunks if estimate_tokens(c) > 0]
    
    print(f"      Final count: {len(chunks)} chunks to index")
    
    if not chunks:
        print("Error: No chunks generated.")
        return

    # 3. Embed
    print(f"      Loading model: {EMBEDDING_MODEL}")
    model = SentenceTransformer(EMBEDDING_MODEL)
    embeddings = generate_embeddings(chunks, model)
    
    # 4. Create Index
    index = create_faiss_index(embeddings)
    
    # 5. Save
    save_artifacts(index, chunks, FAISS_INDEX_PATH, METADATA_PATH, JSON_OUTPUT_PATH)
    
    print("\n  SUCCESS! Ari's life story indexed.")
    print("=" * 70)

if __name__ == "__main__":
    main()
