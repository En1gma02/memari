/**
 * API Service Layer for Memari Chat
 * Typed client for backend communication
 */

// ==============================================================================
// TYPES
// ==============================================================================

export interface ChatRequest {
    session_id: string;
    message: string;
}

export interface WhatsAppResponse {
    messages: string[];
    tool_calls_made?: string[] | null;
    retrieved_context?: string | null;
    reasoning?: string | null;
}

export interface HealthResponse {
    status: string;
    rag_engine: boolean;
    faiss_vectors: number;
}

export interface EndSessionResponse {
    status: string;
    message: string;
}

// ==============================================================================
// CONFIGURATION
// ==============================================================================

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// ==============================================================================
// API FUNCTIONS
// ==============================================================================

/**
 * Send a chat message to Ari (with retry logic)
 */
export async function sendMessage(
    sessionId: string,
    message: string,
    maxRetries: number = 2
): Promise<WhatsAppResponse> {
    let lastError: Error | null = null;

    for (let attempt = 0; attempt <= maxRetries; attempt++) {
        try {
            const response = await fetch(`${API_BASE_URL}/chat`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    session_id: sessionId,
                    message: message,
                } as ChatRequest),
            });

            if (!response.ok) {
                throw new Error(`Chat API error: ${response.status} ${response.statusText}`);
            }

            return response.json();
        } catch (error) {
            lastError = error as Error;
            console.warn(`Chat API attempt ${attempt + 1} failed:`, error);

            if (attempt < maxRetries) {
                // Wait before retrying (exponential backoff)
                await new Promise(r => setTimeout(r, 500 * (attempt + 1)));
            }
        }
    }

    throw lastError || new Error("Chat API failed after retries");
}

/**
 * Check if the backend is healthy
 */
export async function checkHealth(): Promise<boolean> {
    try {
        const response = await fetch(`${API_BASE_URL}/health`, {
            method: "GET",
        });
        return response.ok;
    } catch {
        return false;
    }
}

/**
 * Get health details
 */
export async function getHealthDetails(): Promise<HealthResponse | null> {
    try {
        const response = await fetch(`${API_BASE_URL}/health`, {
            method: "GET",
        });
        if (!response.ok) return null;
        return response.json();
    } catch {
        return null;
    }
}

/**
 * End a session and trigger indexing
 */
export async function endSession(sessionId: string): Promise<EndSessionResponse> {
    const response = await fetch(`${API_BASE_URL}/end-session`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({
            session_id: sessionId,
        }),
    });

    if (!response.ok) {
        throw new Error(`End session error: ${response.status} ${response.statusText}`);
    }

    return response.json();
}

/**
 * Generate a unique session ID
 */
export function generateSessionId(): string {
    const now = new Date();
    const timestamp = now.toISOString().replace(/[-:T.Z]/g, "").slice(0, 14);
    return `session_${timestamp}`;
}
