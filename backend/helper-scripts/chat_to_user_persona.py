"""
chat_to_user_persona.py - Generate User Persona from Indexed Chat Sessions

This script reads all indexed session data and uses Cerebras LLaMA 3.1 8B
to generate a concise, actionable user persona document.

Usage: Run from backend/helper-scripts/ directory
    python chat_to_user_persona.py

Output:
    - backend/user_persona.md: Structured user persona document
"""

import os
import sys
import pickle
from cerebras.cloud.sdk import Cerebras
from dotenv import load_dotenv


# ==============================================================================
# CONFIGURATION
# ==============================================================================

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(SCRIPT_DIR, "..", ".env")
load_dotenv(ENV_PATH)

METADATA_PATH = os.path.join(SCRIPT_DIR, "..", "data", "metadata.pkl")
PERSONA_OUTPUT_PATH = os.path.join(SCRIPT_DIR, "..", "data", "user_persona.md")

CEREBRAS_MODEL = "gpt-oss-120b"


# ==============================================================================
# PERSONA EXTRACTION SYSTEM PROMPT
# ==============================================================================

PERSONA_SYSTEM_PROMPT = """You are an expert User Persona Analyst for an AI chatbot's memory system.

Your task is to analyze conversation history and extract ONLY the most essential, actionable persona traits. This persona will be used by the AI to personalize future conversations.

## Critical Guidelines:

1. **BE EXTREMELY SELECTIVE**: Only include information that would genuinely help personalize conversations. Avoid bloat.

2. **NO PSEUDO-MEMORY**: Don't document every conversation topic. Focus on enduring traits, preferences, and facts.

3. **PRIORITIZE**:
   - Core personality traits
   - Strong preferences (foods, activities, communication style)
   - Important life facts (job, location, family)
   - Recurring interests or hobbies
   - Communication preferences

4. **EXCLUDE**:
   - One-time events or casual mentions
   - Generic small talk topics
   - Temporary states (was tired, had a cold)
   - Things everyone does (eats, sleeps, works)

5. **FORMAT**: Use a clean markdown structure with these sections:
   - **Identity**: Name, occupation, location (if known)
   - **Personality**: Core traits, communication style
   - **Interests & Hobbies**: Recurring activities they enjoy
   - **Preferences**: Strong likes/dislikes
   - **Notable Facts**: Important life details worth remembering

6. **LENGTH**: Keep the entire persona under 300 words. Quality over quantity.

7. **TONE**: Write in third person, present tense. Be factual and concise.

Output ONLY the markdown persona document. No preamble or explanation."""


USER_PROMPT_TEMPLATE = """Analyze the following conversation sessions and extract a concise user persona.

Remember: Be extremely selective. Only include traits and facts that would genuinely help personalize future AI conversations. Avoid documenting everything - focus on what makes this user unique.

---SESSION DATA START---
{sessions}
---SESSION DATA END---

Generate the user persona markdown document:"""


# ==============================================================================
# FUNCTIONS
# ==============================================================================

def load_sessions() -> list[str]:
    """Load all rewritten sessions from metadata."""
    print(f"[1/3] Loading sessions from: {METADATA_PATH}")
    
    if not os.path.exists(METADATA_PATH):
        print(f"ERROR: Metadata file not found at {METADATA_PATH}")
        print("       Run index_chat.py first to generate the index.")
        sys.exit(1)
    
    with open(METADATA_PATH, "rb") as f:
        metadata = pickle.load(f)
    
    id_to_text = metadata.get("id_to_text", {})
    sessions = [id_to_text[i] for i in sorted(id_to_text.keys())]
    
    print(f"      Loaded {len(sessions)} sessions")
    total_chars = sum(len(s) for s in sessions)
    print(f"      Total characters: {total_chars:,}")
    
    return sessions


def generate_persona(sessions: list[str], client: Cerebras) -> str:
    """Use LLM to generate user persona from all sessions."""
    print(f"\n[2/3] Generating persona with {CEREBRAS_MODEL}...")
    
    # Combine all sessions into one context
    # Truncate if too long (keep under ~30K chars for context window)
    combined = "\n\n---\n\n".join(sessions)
    if len(combined) > 30000:
        print(f"      Truncating sessions to fit context window...")
        combined = combined[:30000]
    
    print(f"      Sending {len(combined):,} characters to LLM...")
    
    try:
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": PERSONA_SYSTEM_PROMPT},
                {"role": "user", "content": USER_PROMPT_TEMPLATE.format(sessions=combined)}
            ],
            model=CEREBRAS_MODEL,
            max_tokens=1024,
            temperature=0.3,
        )
        
        persona = response.choices[0].message.content.strip()
        print(f"      Persona generated! ({len(persona)} characters)")
        return persona
        
    except Exception as e:
        print(f"ERROR: Failed to generate persona: {e}")
        sys.exit(1)


def save_persona(persona: str) -> None:
    """Save persona to markdown file."""
    print(f"\n[3/3] Saving persona to: {PERSONA_OUTPUT_PATH}")
    
    # Add header
    full_content = f"""# User Persona

> Auto-generated from {METADATA_PATH} using Cerebras {CEREBRAS_MODEL}
> This document captures core personality traits and preferences for AI personalization.

---

{persona}
"""
    
    with open(PERSONA_OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(full_content)
    
    print(f"      Saved successfully!")


def main():
    """Main execution flow."""
    print("=" * 60)
    print("  MEMARI - User Persona Generator")
    print("  Extracting personality from conversation history")
    print("=" * 60)
    print()
    
    # Validate API key
    api_key = os.environ.get("CEREBRAS_API_KEY")
    if not api_key:
        print("ERROR: CEREBRAS_API_KEY not found in environment!")
        sys.exit(1)
    
    # Initialize client
    client = Cerebras(api_key=api_key)
    print("[*] Cerebras client initialized")
    
    # Load sessions
    sessions = load_sessions()
    
    # Generate persona
    persona = generate_persona(sessions, client)
    
    # Save persona
    save_persona(persona)
    
    # Summary
    print()
    print("=" * 60)
    print("  SUCCESS! User persona generated.")
    print("=" * 60)
    print(f"  Output: {os.path.abspath(PERSONA_OUTPUT_PATH)}")
    print()
    print("  Preview:")
    print("-" * 60)
    # Print first 500 chars as preview
    preview = persona[:500] + "..." if len(persona) > 500 else persona
    print(preview)
    print("=" * 60)


if __name__ == "__main__":
    main()
