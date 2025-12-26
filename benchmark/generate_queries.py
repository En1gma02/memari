"""
generate_queries.py - Generate 100 Benchmark Queries with LLM Morphing

This script:
1. Randomly samples 100 rows from indian_law_dataset.json
2. Uses Cerebras LLM to morph/rephrase each prompt for variation
3. Saves queries.json with ground truth chunk IDs

Usage: python generate_queries.py
"""

import os
import sys
import json
import random
from tqdm import tqdm
from dotenv import load_dotenv
from cerebras.cloud.sdk import Cerebras
import time

# ==============================================================================
# CONFIGURATION
# ==============================================================================

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_ENV = os.path.join(SCRIPT_DIR, "..", "backend", ".env")
DATASET_PATH = os.path.join(SCRIPT_DIR, "indian_law_dataset.json")
OUTPUT_PATH = os.path.join(SCRIPT_DIR, "queries.json")

# Load environment variables from backend/.env
load_dotenv(BACKEND_ENV)

# Number of queries to generate
NUM_QUERIES = 100

# Cerebras configuration
CEREBRAS_MODEL = "gpt-oss-120b"

# ==============================================================================
# LLM MORPHING
# ==============================================================================

def morph_query(client: Cerebras, original_query: str) -> str:
    """
    Use LLM to rephrase/morph a query while preserving its intent.
    """
    prompt = f"""Rephrase the following legal question to ask the same thing in a different way. 
Keep the meaning identical but change the wording, structure, or phrasing. Include some Hinglish text and elements too.
Return ONLY the rephrased question, nothing else.

Original question: {original_query}

Rephrased question:"""

    try:
        response = client.chat.completions.create(
            model=CEREBRAS_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=512,
            temperature=0.65,
            reasoning_effort="high",
        )
        
        # Handle potential None response
        if response and response.choices and len(response.choices) > 0:
            message = response.choices[0].message
            if message and message.content:
                morphed = message.content.strip()
                # Clean up any quotes or prefixes
                morphed = morphed.strip('"\'')
                if morphed.lower().startswith("rephrased question:"):
                    morphed = morphed[19:].strip()
                return morphed if morphed else original_query
        
        return original_query
    except Exception as e:
        print(f"  ⚠️ LLM morph failed: {e}")
        return original_query


def main():
    print("=" * 70)
    print("  RAG Benchmark - Query Generator (LLM Morphing)")
    print("=" * 70)
    
    # Check API key
    api_key = os.environ.get("CEREBRAS_API_KEY")
    if not api_key:
        print("ERROR: CEREBRAS_API_KEY not set in environment")
        sys.exit(1)
    
    # Initialize Cerebras client
    print("\n[1/4] Initializing Cerebras client...")
    client = Cerebras(api_key=api_key)
    
    # Load dataset
    print(f"\n[2/4] Loading dataset: {DATASET_PATH}")
    if not os.path.exists(DATASET_PATH):
        print(f"ERROR: Dataset not found at {DATASET_PATH}")
        sys.exit(1)
    
    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    print(f"      Loaded {len(data)} records")
    
    # Random sample
    print(f"\n[3/4] Randomly sampling {NUM_QUERIES} records...")
    if len(data) < NUM_QUERIES:
        print(f"WARNING: Dataset has only {len(data)} records, using all")
        sampled_indices = list(range(len(data)))
    else:
        sampled_indices = random.sample(range(len(data)), NUM_QUERIES)
    
    # Generate morphed queries
    print(f"\n[4/4] Generating morphed queries with LLM...")
    queries = []
    
    for i, idx in enumerate(tqdm(sampled_indices, desc="Morphing queries")):
        record = data[idx]
        original_prompt = record.get("prompt", "").strip()
        expected_response = record.get("response", "").strip()
        
        if not original_prompt:
            continue
        
        # Morph the query
        morphed_query = morph_query(client, original_prompt)
        time.sleep(2)
        
        query_entry = {
            "id": i,
            "original_query": original_prompt,
            "query": morphed_query,
            "expected_chunk_id": idx,  # Ground truth: the chunk this came from
            "expected_response": expected_response
        }
        queries.append(query_entry)
    
    # Save queries
    print(f"\n      Generated {len(queries)} queries")
    
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(queries, f, indent=2, ensure_ascii=False)
    
    print(f"      Saved to: {OUTPUT_PATH}")
    
    # Show samples
    print("\n" + "=" * 70)
    print("  Sample Queries (first 3):")
    print("=" * 70)
    for q in queries[:3]:
        print(f"\n  ID: {q['id']}")
        print(f"  Original: {q['original_query'][:80]}...")
        print(f"  Morphed:  {q['query'][:80]}...")
        print(f"  Ground Truth Chunk: {q['expected_chunk_id']}")
    
    print("\n" + "=" * 70)
    print("  SUCCESS! Query generation complete.")
    print("=" * 70)


if __name__ == "__main__":
    main()
