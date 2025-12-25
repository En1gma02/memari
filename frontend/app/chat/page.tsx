"use client";

import { useState, useEffect, useCallback } from "react";
import { ChatInterface, ChatHistory, DebugPanel, ContextChunk } from "@/components/chat";
import {
    sendMessage,
    checkHealth,
    generateSessionId,
} from "@/lib/api";

interface Message {
    id: string;
    role: "user" | "assistant";
    content: string[];
    timestamp: Date;
    status?: "sending" | "sent" | "delivered";
}

interface DebugInfo {
    toolsCalled: string[];
    contextChunks: ContextChunk[];
}

export default function ChatPage() {
    const [sessionId, setSessionId] = useState<string>("");
    const [messages, setMessages] = useState<Message[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [isOnline, setIsOnline] = useState(true);
    const [debugInfo, setDebugInfo] = useState<DebugInfo>({
        toolsCalled: [],
        contextChunks: [],
    });

    useEffect(() => {
        setSessionId(generateSessionId());
        checkHealth().then(setIsOnline);
        const interval = setInterval(() => {
            checkHealth().then(setIsOnline);
        }, 30000);
        return () => clearInterval(interval);
    }, []);

    const handleSendMessage = useCallback(
        async (messageText: string) => {
            if (!messageText.trim() || isLoading) return;

            const timestamp = new Date();
            const userMessage: Message = {
                id: `user-${Date.now()}`,
                role: "user",
                content: [messageText],
                timestamp,
                status: "sending",
            };
            setMessages((prev) => [...prev, userMessage]);
            setIsLoading(true);

            setTimeout(() => {
                setMessages((prev) =>
                    prev.map((m) => (m.id === userMessage.id ? { ...m, status: "sent" } : m))
                );
            }, 300);

            try {
                const response = await sendMessage(sessionId, messageText);

                setMessages((prev) =>
                    prev.map((m) => (m.id === userMessage.id ? { ...m, status: "delivered" } : m))
                );

                const assistantMessage: Message = {
                    id: `assistant-${Date.now()}`,
                    role: "assistant",
                    content: response.messages,
                    timestamp: new Date(),
                };
                setMessages((prev) => [...prev, assistantMessage]);

                const chunks: ContextChunk[] = [];
                if (response.retrieved_context) {
                    // Try to parse numbered chunks like "1. (Score: 0.482)\nText..."
                    const numberedPattern = /(\d+)\.\s*\(Score:\s*([\d.]+)\)\s*([\s\S]*?)(?=\d+\.\s*\(Score:|$)/g;
                    let match;
                    while ((match = numberedPattern.exec(response.retrieved_context)) !== null) {
                        const score = parseFloat(match[2]);
                        const text = match[3].trim();
                        if (text) {
                            chunks.push({ text, score });
                        }
                    }

                    // Fallback: split by --- if no numbered chunks found
                    if (chunks.length === 0) {
                        const contextParts = response.retrieved_context.split("\n\n---\n\n");
                        contextParts.forEach((part, i) => {
                            if (part.trim()) {
                                chunks.push({ text: part.trim(), score: 1 - i * 0.1 });
                            }
                        });
                    }
                }

                setDebugInfo({
                    toolsCalled: response.tool_calls_made || [],
                    contextChunks: chunks.length > 0 ? chunks : response.retrieved_context
                        ? [{ text: response.retrieved_context }]
                        : [],
                });
            } catch (error) {
                console.error("Chat error:", error);
                const errorMessage: Message = {
                    id: `error-${Date.now()}`,
                    role: "assistant",
                    content: ["Sorry, I encountered an error. Please try again."],
                    timestamp: new Date(),
                };
                setMessages((prev) => [...prev, errorMessage]);
            } finally {
                setIsLoading(false);
            }
        },
        [sessionId, isLoading]
    );

    const handleClearChat = useCallback(() => {
        setMessages([]);
        setDebugInfo({ toolsCalled: [], contextChunks: [] });
        setSessionId(generateSessionId());
    }, []);

    if (!isOnline) {
        return (
            <div className="h-screen flex items-center justify-center bg-background">
                <div className="text-center max-w-md p-8">
                    <div className="w-16 h-16 rounded-full bg-destructive/10 flex items-center justify-center mx-auto mb-4">
                        <span className="text-3xl">⚠️</span>
                    </div>
                    <h2 className="text-xl font-semibold text-foreground mb-2">
                        Backend Unavailable
                    </h2>
                    <p className="text-sm text-muted-foreground mb-4">
                        The backend server is not running. Please start it with:
                    </p>
                    <code className="block bg-card border border-border rounded-lg px-4 py-3 text-sm font-mono text-foreground/90">
                        cd backend && uvicorn main:app --reload
                    </code>
                    <button
                        onClick={() => checkHealth().then(setIsOnline)}
                        className="mt-4 text-sm text-primary hover:underline"
                    >
                        Retry connection
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className="h-screen w-screen overflow-hidden grid grid-cols-[280px_1fr_280px] bg-background">
            {/* Left Pane */}
            <ChatHistory />

            {/* Center Pane */}
            <ChatInterface
                messages={messages}
                onSendMessage={handleSendMessage}
                onClearChat={handleClearChat}
                isLoading={isLoading}
                isOnline={isOnline}
            />

            {/* Right Pane */}
            <DebugPanel debugInfo={debugInfo} sessionId={sessionId} />
        </div>
    );
}
