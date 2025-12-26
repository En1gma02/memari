"""
verify_ari_index.py - Verify Ari Life Indexing
"""
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from rag_engine import get_rag_engine

def main():
    print("Initializing RAG Engine...")
    engine = get_rag_engine()
    
    if engine.ari_index is None:
        print("ERROR: Ari index not loaded!")
        return

    print(f"Ari Index Size: {engine.ari_index.ntotal}")
    
    query = "What is Ari's favorite food?"
    print(f"\nQuerying: '{query}'")
    
    result = engine.get_ari_life_memory(query)
    
    print(f"Found {len(result.chunks)} chunks.")
    for i, (chunk, score) in enumerate(zip(result.chunks, result.scores)):
        print(f"\n[{i+1}] Score: {score:.3f}")
        print(chunk[:200].replace("\n", " ") + "...")

if __name__ == "__main__":
    main()
