"""
index_to_json.py - Export FAISS Index Metadata to JSON

This script reads the metadata.pkl file and exports all indexed
chunks to a readable JSON format for inspection.

Usage: Run from backend/helper-scripts/ directory
    python index_to_json.py

Output:
    - backend/helper-scripts/chat_index.json
"""

import os
import sys
import json
import pickle


# ==============================================================================
# CONFIGURATION
# ==============================================================================

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
METADATA_PATH = os.path.join(SCRIPT_DIR, "..", "data", "metadata.pkl")
OUTPUT_JSON_PATH = os.path.join(SCRIPT_DIR, "..", "data", "chat_index.json")


def estimate_tokens(text: str) -> int:
    """
    Estimate token count for a text string.
    
    Rule of thumb: ~4 characters per token for English text.
    This is an approximation; actual tokenization varies by model.
    
    Args:
        text: Input text string
        
    Returns:
        Estimated token count
    """
    return len(text) // 4


def main():
    """Main execution flow."""
    print("=" * 60)
    print("  MEMARI - Index to JSON Exporter")
    print("=" * 60)
    print()
    
    # Step 1: Load metadata
    print(f"[1/3] Loading metadata from: {METADATA_PATH}")
    
    if not os.path.exists(METADATA_PATH):
        print(f"ERROR: Metadata file not found at {METADATA_PATH}")
        print("       Run index_chat.py first to generate the index.")
        sys.exit(1)
    
    with open(METADATA_PATH, "rb") as f:
        metadata = pickle.load(f)
    
    print(f"      Metadata loaded successfully!")
    print(f"      Total sessions: {metadata.get('total_sessions', 'N/A')}")
    print(f"      Embedding model: {metadata.get('embedding_model', 'N/A')}")
    print(f"      Rewrite model: {metadata.get('rewrite_model', 'N/A')}")
    
    # Step 2: Convert to JSON format
    print(f"\n[2/3] Converting chunks to JSON format...")
    
    id_to_text = metadata.get("id_to_text", {})
    id_to_original = metadata.get("id_to_original", {})
    
    chunks = []
    total_chars = 0
    total_tokens = 0
    
    for session_id in sorted(id_to_text.keys()):
        chunk_text = id_to_text[session_id]
        original_text = id_to_original.get(session_id, "")
        
        num_chars = len(chunk_text)
        num_tokens = estimate_tokens(chunk_text)
        
        chunk_obj = {
            "session_id": session_id,
            "chunk_text": chunk_text,
            "original_text": original_text,
            "number_of_chars": num_chars,
            "number_of_tokens": num_tokens
        }
        
        chunks.append(chunk_obj)
        total_chars += num_chars
        total_tokens += num_tokens
        
        # Progress log
        print(f"      [{session_id + 1}/{len(id_to_text)}] Session {session_id}: {num_chars} chars, ~{num_tokens} tokens")
    
    # Step 3: Save to JSON
    print(f"\n[3/3] Saving to JSON: {OUTPUT_JSON_PATH}")
    
    output_data = {
        "metadata": {
            "total_sessions": len(chunks),
            "total_chars": total_chars,
            "total_tokens": total_tokens,
            "embedding_model": metadata.get("embedding_model", ""),
            "rewrite_model": metadata.get("rewrite_model", ""),
            "embedding_dimension": metadata.get("embedding_dimension", 0)
        },
        "chunks": chunks
    }
    
    with open(OUTPUT_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    file_size = os.path.getsize(OUTPUT_JSON_PATH) / 1024
    print(f"      JSON saved successfully! ({file_size:.2f} KB)")
    
    # Summary
    print()
    print("=" * 60)
    print("  EXPORT COMPLETE - Database Statistics")
    print("=" * 60)
    print(f"  Total Sessions:  {len(chunks)}")
    print(f"  Total Chars:     {total_chars:,}")
    print(f"  Total Tokens:    ~{total_tokens:,} (estimated)")
    print(f"  Avg Chars/Chunk: {total_chars // len(chunks) if chunks else 0}")
    print(f"  Avg Tokens/Chunk: ~{total_tokens // len(chunks) if chunks else 0}")
    print()
    print(f"  Output: {os.path.abspath(OUTPUT_JSON_PATH)}")
    print("=" * 60)


if __name__ == "__main__":
    main()
