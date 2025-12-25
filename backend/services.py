"""
services.py - Business Logic Services for Ari Chatbot

Contains:
- ChatService: Handles chat flow, safety, tool calling
- RAG Engine logic is in rag_engine.py (will be updated for hybrid search)
"""

import json
import time
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from groq import Groq

from config import (
    GROQ_API_KEY, 
    GROQ_CHAT_MODEL, 
    GROQ_SAFETY_MODEL, 
    TEMPERATURE, 
    MAX_TOKENS
)
from models import WhatsAppResponse, SafetyCheckResult
from prompts import ARI_SYSTEM_PROMPT, TOOL_DEFINITIONS
from rag_engine import get_rag_engine


# ==============================================================================
# SESSION STORAGE (in-memory for MVP)
# ==============================================================================

session_history: Dict[str, List[Dict[str, str]]] = {}
session_last_activity: Dict[str, datetime] = {}


# ==============================================================================
# CHAT SERVICE
# ==============================================================================

class ChatService:
    """
    Handles chat flow with proper tool use pattern:
    1. Single API call with tools
    2. Execute tools if requested
    3. Send tool results back
    4. Model returns final answer
    
    Uses prompt caching optimization:
    - Static content (system prompt, tools) at beginning
    - Dynamic content (user message) at end
    """
    
    def __init__(self):
        self.groq_client = Groq(api_key=GROQ_API_KEY)
        self.rag_engine = None
    
    def _get_rag_engine(self):
        """Lazy load RAG engine."""
        if self.rag_engine is None:
            self.rag_engine = get_rag_engine()
        return self.rag_engine
    
    def check_safety(self, message: str) -> SafetyCheckResult:
        """
        Check message safety using Llama Guard 4.
        
        Args:
            message: User message to check
        
        Returns:
            SafetyCheckResult with safety status
        """
        try:
            response = self.groq_client.chat.completions.create(
                model=GROQ_SAFETY_MODEL,
                messages=[{"role": "user", "content": message}]
            )
            
            raw_output = response.choices[0].message.content.strip()
            
            # Llama Guard returns "safe" or "unsafe\nS2" (with category)
            is_safe = raw_output.lower() == "safe"
            violation_category = None
            
            if not is_safe:
                lines = raw_output.split("\n")
                if len(lines) > 1:
                    violation_category = lines[1]
            
            return SafetyCheckResult(
                is_safe=is_safe,
                violation_category=violation_category,
                raw_output=raw_output
            )
        
        except Exception as e:
            print(f"⚠️  Safety check error: {e}")
            # Default to safe if check fails (fail open)
            return SafetyCheckResult(
                is_safe=True,
                violation_category=None,
                raw_output="error"
            )
    
    def execute_tool(self, tool_name: str, tool_args: Dict[str, Any]) -> str:
        """
        Execute a tool call locally.
        
        Args:
            tool_name: Name of the tool to execute
            tool_args: Arguments for the tool
        
        Returns:
            Tool execution result as string
        """
        rag_engine = self._get_rag_engine()
        
        if tool_name == "get_user_persona":
            persona = rag_engine.get_user_persona()
            return f"User Persona:\n{persona}"
        
        elif tool_name == "get_long_term_memory":
            query = tool_args.get("query", "")
            if not query:
                return "Error: No query provided"
            
            result = rag_engine.get_long_term_memory(query)
            
            if not result.chunks:
                return "No relevant memories found."
            
            # Format the memory results
            formatted = "Retrieved Memories:\n\n"
            for i, (chunk, score) in enumerate(zip(result.chunks, result.scores), 1):
                formatted += f"{i}. (Score: {score:.3f})\n{chunk}\n\n"
            
            if result.fusion_used:
                formatted += "(Used fusion retrieval for better results)"
            
            return formatted
        
        else:
            return f"Error: Unknown tool '{tool_name}'"
    
    def chat(
        self, 
        session_id: str, 
        message: str
    ) -> Tuple[WhatsAppResponse, SafetyCheckResult]:
        """
        Main chat function with proper tool use flow.
        
        Flow (per Groq docs):
        1. Safety check
        2. Build messages (static content first for caching)
        3. Call LLM with tools
        4. If tool_calls: execute tools, add results, call LLM again
        5. Model returns final answer directly
        
        Args:
            session_id: Session identifier
            message: User message
        
        Returns:
            Tuple of (WhatsAppResponse, SafetyCheckResult)
        """
        # Step 1: Safety Check
        print(f"🔒 Safety check for session: {session_id}")
        safety_result = self.check_safety(message)
        
        if not safety_result.is_safe:
            print(f"⚠️  Unsafe content detected: {safety_result.violation_category}")
            return WhatsAppResponse(
                messages=[
                    "Arre yaar, let's talk about something else! 😅",
                    "Koi aur topic discuss karte hain?"
                ]
            ), safety_result
        
        # Step 2: Get or initialize session history
        if session_id not in session_history:
            session_history[session_id] = []
        
        session_history[session_id].append({
            "role": "user",
            "content": message
        })
        
        session_last_activity[session_id] = datetime.now()
        
        # Step 3: Build messages for LLM
        # PROMPT CACHING: Static content (system prompt + tools) first
        # Dynamic content (conversation history) last
        messages = [
            {"role": "system", "content": ARI_SYSTEM_PROMPT}
        ] + session_history[session_id]
        
        # Step 4: Tool-calling loop (max 3 iterations for safety)
        max_iterations = 3
        iteration = 0
        tool_calls_made = []
        retrieved_context = ""
        
        while iteration < max_iterations:
            iteration += 1
            
            try:
                # Call LLM with tools
                # Tools are also cached (static content)
                response = self.groq_client.chat.completions.create(
                    model=GROQ_CHAT_MODEL,
                    messages=messages,
                    tools=TOOL_DEFINITIONS,
                    temperature=TEMPERATURE,
                    max_tokens=MAX_TOKENS
                )
                
                assistant_message = response.choices[0].message
                
                # Check if model wants to use tools
                if assistant_message.tool_calls:
                    print(f"🔧 Tool calls requested: {len(assistant_message.tool_calls)}")
                    
                    # Add assistant message with tool calls to history
                    messages.append({
                        "role": "assistant",
                        "content": assistant_message.content or "",
                        "tool_calls": [
                            {
                                "id": tc.id,
                                "type": "function",
                                "function": {
                                    "name": tc.function.name,
                                    "arguments": tc.function.arguments
                                }
                            }
                            for tc in assistant_message.tool_calls
                        ]
                    })
                    
                    # Execute each tool
                    for tool_call in assistant_message.tool_calls:
                        tool_name = tool_call.function.name
                        tool_args = json.loads(tool_call.function.arguments)
                        
                        print(f"  Executing: {tool_name}({tool_args})")
                        tool_calls_made.append(tool_name)
                        
                        # Execute tool
                        start_time = time.time()
                        tool_result = self.execute_tool(tool_name, tool_args)
                        execution_time = (time.time() - start_time) * 1000
                        
                        print(f"  ✓ Completed in {execution_time:.2f}ms")
                        
                        # Store context for Memory Panel
                        if tool_name == "get_long_term_memory":
                            retrieved_context = tool_result
                        
                        # Add tool result to messages
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "name": tool_name,
                            "content": tool_result
                        })
                    
                    # Continue loop - model will process tool results
                    continue
                
                # Step 5: Model returned final answer (no more tool calls)
                else:
                    print("💬 Got final response from model")
                    
                    response_content = assistant_message.content
                    
                    # Parse the JSON response
                    try:
                        response_json = json.loads(response_content)
                        response_messages = response_json.get("messages", [response_content])
                    except json.JSONDecodeError:
                        # Fallback: split by newlines or use as single message
                        print(f"⚠️  Response not JSON, using as-is")
                        if "\n" in response_content:
                            response_messages = [
                                line.strip() 
                                for line in response_content.split("\n") 
                                if line.strip()
                            ][:10]  # Max 10 bubbles
                        else:
                            response_messages = [response_content]
                    
                    # Add to session history
                    session_history[session_id].append({
                        "role": "assistant",
                        "content": response_content
                    })
                    
                    return WhatsAppResponse(
                        messages=response_messages,
                        tool_calls_made=tool_calls_made if tool_calls_made else None,
                        retrieved_context=retrieved_context if retrieved_context else None
                    ), safety_result
            
            except Exception as e:
                error_str = str(e)
                print(f"❌ Error in chat loop: {e}")
                
                # Handle tool_use_failed error - extract valid response from error
                if "tool_use_failed" in error_str and "failed_generation" in error_str:
                    print("⚠️  Extracting response from failed_generation...")
                    try:
                        # Extract the failed_generation JSON from error
                        import re
                        # Match the JSON object in failed_generation
                        match = re.search(r"'failed_generation': '(\{.+\})'", error_str, re.DOTALL)
                        if match:
                            failed_json_str = match.group(1)
                            # Unescape the string
                            failed_json_str = failed_json_str.replace("\\n", "\n").replace("\\'", "'")
                            response_json = json.loads(failed_json_str)
                            
                            # Handle both {"messages": [...]} and {"arguments": {"messages": [...]}}
                            if "arguments" in response_json and "messages" in response_json["arguments"]:
                                response_messages = response_json["arguments"]["messages"]
                            elif "messages" in response_json:
                                response_messages = response_json["messages"]
                            else:
                                response_messages = []
                            
                            if response_messages:
                                print(f"✓ Recovered {len(response_messages)} messages from failed_generation")
                                
                                # Add to session history
                                session_history[session_id].append({
                                    "role": "assistant",
                                    "content": json.dumps({"messages": response_messages})
                                })
                                
                                return WhatsAppResponse(
                                    messages=response_messages,
                                    tool_calls_made=tool_calls_made if tool_calls_made else None,
                                    retrieved_context=retrieved_context if retrieved_context else None
                                ), safety_result
                    except Exception as parse_error:
                        print(f"❌ Failed to parse failed_generation: {parse_error}")
                
                raise e
        
        # Max iterations reached
        return WhatsAppResponse(
            messages=[
                "Sorry yaar, itna complex ho gaya! 😅",
                "Ek baar phir se try karte hain?"
            ]
        ), safety_result
    
    def get_session_history(self, session_id: str) -> List[Dict[str, str]]:
        """Get history for a session."""
        return session_history.get(session_id, [])
    
    def clear_session(self, session_id: str):
        """Clear session history."""
        if session_id in session_history:
            del session_history[session_id]
        if session_id in session_last_activity:
            del session_last_activity[session_id]


# ==============================================================================
# SINGLETON
# ==============================================================================

_chat_service: Optional[ChatService] = None


def get_chat_service() -> ChatService:
    """Get or create the chat service singleton."""
    global _chat_service
    if _chat_service is None:
        _chat_service = ChatService()
    return _chat_service
