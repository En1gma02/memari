"""
index_data.py - Index Indian Law Dataset for RAG Benchmarking

This script processes benchmark/indian_law_dataset.json:
1. Treats each JSON object (prompt, complex_cot, response) as a single chunk.
2. Generates embeddings using sentence-transformers.
3. Saves a FAISS index (benchmark_faiss_index.bin).
4. Saves metadata (benchmark_metadata.pkl).
5. Exports a compact JSON with only metadata stats (index.json).

Dataset Format:
[
    { "prompt": "", "complex_cot": "", "response": "" },
    ...
]

Usage: Run from benchmark/ directory
    python index_data.py
"""

import os
import sys
import json
import pickle
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from typing import List, Dict
from tqdm import tqdm

# ==============================================================================
# CONFIGURATION
# ==============================================================================

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_PATH = os.path.join(SCRIPT_DIR, "indian_law_dataset.json")
FAISS_INDEX_PATH = os.path.join(SCRIPT_DIR, "benchmark_faiss_index.bin")
METADATA_PATH = os.path.join(SCRIPT_DIR, "benchmark_metadata.pkl")
JSON_OUTPUT_PATH = os.path.join(SCRIPT_DIR, "index.json")

# Model configuration (matching main project)
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIMENSION = 384

# Token estimation
CHARS_PER_TOKEN = 4  # Approximation

# Batch size for embedding generation (to avoid OOM with large datasets)
EMBEDDING_BATCH_SIZE = 512

# ==============================================================================
# FUNCTIONS
# ==============================================================================

def estimate_tokens(text: str) -> int:
    """Estimate token count based on characters."""
    return len(text) // CHARS_PER_TOKEN


def load_dataset(file_path: str) -> List[Dict]:
    """Load the JSON dataset."""
    print(f"[1/5] Loading dataset: {file_path}")
    if not os.path.exists(file_path):
        print(f"ERROR: Dataset not found at {file_path}")
        sys.exit(1)
    
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    print(f"      Loaded {len(data)} records")
    return data


def create_chunks_from_dataset(data: List[Dict]) -> List[str]:
    """
    Create chunks from dataset.
    Each JSON object (prompt + complex_cot + response) is treated as a single chunk.
    """
    print(f"\n[2/5] Creating chunks from {len(data)} records...")
    chunks = []
    
    for record in tqdm(data, desc="Processing records"):
        # Combine all fields into a single chunk
        # Format: structured text with labeled sections
        prompt = record.get("prompt", "").strip()
        complex_cot = record.get("complex_cot", "").strip()
        response = record.get("response", "").strip()
        
        # Create a unified chunk that preserves the structure
        chunk_parts = []
        if prompt:
            chunk_parts.append(f"Question: {prompt}")
        if complex_cot:
            chunk_parts.append(f"Chain of Thought: {complex_cot}")
        if response:
            chunk_parts.append(f"Answer: {response}")
        
        chunk = "\n\n".join(chunk_parts)
        
        if chunk.strip():  # Only add non-empty chunks
            chunks.append(chunk)
    
    print(f"      Created {len(chunks)} chunks")
    return chunks


def generate_embeddings(chunks: List[str], model: SentenceTransformer) -> np.ndarray:
    """Generate embeddings for chunks in batches."""
    print(f"\n[3/5] Generating embeddings for {len(chunks)} chunks...")
    print(f"      Using batch size: {EMBEDDING_BATCH_SIZE}")
    
    all_embeddings = []
    total_batches = (len(chunks) + EMBEDDING_BATCH_SIZE - 1) // EMBEDDING_BATCH_SIZE
    
    for i in tqdm(range(0, len(chunks), EMBEDDING_BATCH_SIZE), desc="Embedding batches", total=total_batches):
        batch = chunks[i:i + EMBEDDING_BATCH_SIZE]
        batch_embeddings = model.encode(batch, show_progress_bar=False)
        all_embeddings.append(batch_embeddings)
    
    embeddings = np.vstack(all_embeddings).astype("float32")
    print(f"      Generated embeddings shape: {embeddings.shape}")
    return embeddings


def create_faiss_index(embeddings: np.ndarray) -> faiss.IndexFlatL2:
    """Create FAISS index."""
    print(f"\n[4/5] Creating FAISS index...")
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings)
    print(f"      Index created with {index.ntotal} vectors")
    return index


def save_artifacts(index, chunks: List[str], data: List[Dict], index_path: str, 
                   metadata_path: str, json_path: str):
    """Save index, metadata, and compact JSON."""
    print(f"\n[5/5] Saving artifacts...")
    
    # Calculate stats
    total_chunks = len(chunks)
    total_chars = sum(len(c) for c in chunks)
    total_tokens = sum(estimate_tokens(c) for c in chunks)
    avg_tokens = round(total_tokens / total_chunks, 2) if total_chunks else 0
    
    print(f"      Stats: {total_chunks:,} chunks, {total_tokens:,} tokens total")
    print(f"      Avg: {avg_tokens} tokens/chunk")
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(index_path) if os.path.dirname(index_path) else ".", exist_ok=True)
    
    # 1. Save FAISS index
    faiss.write_index(index, index_path)
    print(f"      FAISS index saved: {index_path}")
    
    # 2. Save Metadata (includes full text for retrieval)
    metadata = {
        "id_to_text": {i: text for i, text in enumerate(chunks)},
        "id_to_original": {i: data[i] for i in range(len(data)) if i < len(chunks)},
        "total_chunks": len(chunks),
        "embedding_model": EMBEDDING_MODEL,
        "source": "indian_law_dataset.json"
    }
    
    with open(metadata_path, "wb") as f:
        pickle.dump(metadata, f)
    print(f"      Metadata saved: {metadata_path}")
    
    # 3. Save compact JSON (only metadata stats, no chunks)
    json_data = {
        "total_chunks": total_chunks,
        "total_tokens": total_tokens,
        "avg_tokens_per_chunk": avg_tokens
    }
    
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(json_data, f, indent=2)
    print(f"      JSON stats saved: {json_path}")


def main():
    print("=" * 70)
    print("  MEMARI - Benchmark Dataset Indexer")
    print("  Dataset: Indian Law (~50M tokens)")
    print("=" * 70)

    # 1. Load dataset
    data = load_dataset(DATASET_PATH)
    
    if not data:
        print("Error: Empty dataset.")
        return
    
    # 2. Create chunks (each record = 1 chunk)
    chunks = create_chunks_from_dataset(data)
    
    if not chunks:
        print("Error: No chunks generated.")
        return

    # 3. Load embedding model
    print(f"\n      Loading model: {EMBEDDING_MODEL}")
    model = SentenceTransformer(EMBEDDING_MODEL)
    
    # 4. Generate embeddings
    embeddings = generate_embeddings(chunks, model)
    
    # 5. Create FAISS index
    index = create_faiss_index(embeddings)
    
    # 6. Save artifacts
    save_artifacts(index, chunks, data, FAISS_INDEX_PATH, METADATA_PATH, JSON_OUTPUT_PATH)
    
    print("\n" + "=" * 70)
    print("  SUCCESS! Indian Law dataset indexed for benchmarking.")
    print("=" * 70)


if __name__ == "__main__":
    main()
