/**
 * Data loading utilities for chat history and user persona
 */

export interface ChatMessage {
    role: "human" | "ari";
    content: string;
}

/**
 * Fetch chat history from backend data
 */
export async function fetchChatHistory(): Promise<string> {
    try {
        const response = await fetch("/api/data?file=CHAT.txt");
        if (!response.ok) throw new Error("Failed to fetch chat history");
        const data = await response.json();
        return data.content;
    } catch (error) {
        console.error("Error fetching chat history:", error);
        return "";
    }
}

/**
 * Fetch user persona markdown
 */
export async function fetchUserPersona(): Promise<string> {
    try {
        const response = await fetch("/api/data?file=user-persona.md");
        if (!response.ok) throw new Error("Failed to fetch user persona");
        const data = await response.json();
        return data.content;
    } catch (error) {
        console.error("Error fetching user persona:", error);
        return "";
    }
}


/**
 * Fetch Ari's life story markdown
 */
export async function fetchAriLifeContent(): Promise<string> {
    try {
        const response = await fetch("/api/ari-life");
        if (!response.ok) throw new Error("Failed to fetch Ari's life content");
        const data = await response.json();
        return data.content;
    } catch (error) {
        console.error("Error fetching Ari's life content:", error);
        return "";
    }
}

/**
 * Parse CHAT.txt content into structured messages
 */
export function parseChatHistory(content: string): ChatMessage[] {
    const messages: ChatMessage[] = [];
    const lines = content.split("\n");

    for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed) continue;

        // Match "Human 1:" or "Ari:" patterns
        const humanMatch = trimmed.match(/^Human \d+:\s*(.*)$/);
        const ariMatch = trimmed.match(/^Ari:\s*(.*)$/);

        if (humanMatch) {
            messages.push({ role: "human", content: humanMatch[1] });
        } else if (ariMatch) {
            messages.push({ role: "ari", content: ariMatch[1] });
        }
    }

    return messages;
}

