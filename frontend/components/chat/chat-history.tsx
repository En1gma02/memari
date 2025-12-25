"use client";

import { useState, useEffect } from "react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { cn } from "@/lib/utils";
import { fetchChatHistory, fetchUserPersona, parseChatHistory, ChatMessage } from "@/lib/data";

type ViewMode = "history" | "persona";

// Database metadata
const DB_METADATA = {
    totalChats: 750,
    totalSessions: 93,
    totalTokens: 29645,
    embeddedTokens: 13255,
};

export function ChatHistory() {
    const [viewMode, setViewMode] = useState<ViewMode>("history");
    const [historyMessages, setHistoryMessages] = useState<ChatMessage[]>([]);
    const [personaContent, setPersonaContent] = useState("");
    const [isLoading, setIsLoading] = useState(false);

    useEffect(() => {
        loadData();
    }, [viewMode]);

    const loadData = async () => {
        setIsLoading(true);
        try {
            if (viewMode === "history") {
                const content = await fetchChatHistory();
                const messages = parseChatHistory(content);
                setHistoryMessages(messages);
            } else {
                const content = await fetchUserPersona();
                setPersonaContent(content);
            }
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="h-screen flex flex-col bg-card/30 backdrop-blur-sm border-r border-border/50">
            {/* Header - Squarish toggle */}
            <div className="h-[72px] px-4 flex items-center border-b border-border/50 shrink-0">
                <div className="flex w-full bg-transparent rounded-lg p-0.5 gap-1">
                    <button
                        onClick={() => setViewMode("history")}
                        title="This is the chat database currently embedded in Ari's long term memory for demonstration purposes."
                        className={cn(
                            "flex-1 px-4 py-2 text-sm font-medium rounded-lg transition-all duration-200",
                            viewMode === "history"
                                ? "bg-primary/20 text-foreground border border-primary/30"
                                : "text-muted-foreground hover:text-foreground hover:bg-card/50"
                        )}
                    >
                        History
                    </button>
                    <button
                        onClick={() => setViewMode("persona")}
                        title="This is the outlined personality of the user which Ari has identified and often uses when needing more context about user."
                        className={cn(
                            "flex-1 px-4 py-2 text-sm font-medium rounded-lg transition-all duration-200",
                            viewMode === "persona"
                                ? "bg-primary/20 text-foreground border border-primary/30"
                                : "text-muted-foreground hover:text-foreground hover:bg-card/50"
                        )}
                    >
                        Persona
                    </button>
                </div>
            </div>

            {/* Scrollable Content */}
            <div className="flex-1 min-h-0 overflow-hidden">
                <ScrollArea className="h-full">
                    <div className="p-4">
                        {isLoading ? (
                            <div className="flex items-center justify-center h-32">
                                <div className="w-6 h-6 border-2 border-primary border-t-transparent rounded-full animate-spin" />
                            </div>
                        ) : viewMode === "history" ? (
                            <HistoryBubbles messages={historyMessages} />
                        ) : (
                            <PersonaView content={personaContent} />
                        )}
                    </div>
                </ScrollArea>
            </div>

            {/* Footer - 2x2 Grid, left aligned, smaller font */}
            <div className="h-[72px] px-4 flex items-center shrink-0 bg-background/30">
                <div className="w-full grid grid-cols-2 gap-x-4 gap-y-0.5">
                    <div className="text-left">
                        <p className="text-xs font-semibold text-foreground">{DB_METADATA.totalSessions}</p>
                        <p className="text-[8px] text-muted-foreground uppercase tracking-wide">Sessions</p>
                    </div>
                    <div className="text-left">
                        <p className="text-xs font-semibold text-foreground">{DB_METADATA.totalChats.toLocaleString()}</p>
                        <p className="text-[8px] text-muted-foreground uppercase tracking-wide">Messages</p>
                    </div>
                    <div className="text-left">
                        <p className="text-xs font-semibold text-foreground">{DB_METADATA.totalTokens.toLocaleString()}</p>
                        <p className="text-[8px] text-muted-foreground uppercase tracking-wide">Tokens</p>
                    </div>
                    <div className="text-left">
                        <p className="text-xs font-semibold text-primary">{DB_METADATA.embeddedTokens.toLocaleString()}</p>
                        <p className="text-[8px] text-muted-foreground uppercase tracking-wide">Embedded</p>
                    </div>
                </div>
            </div>
        </div>
    );
}

function HistoryBubbles({ messages }: { messages: ChatMessage[] }) {
    if (messages.length === 0) {
        return (
            <p className="text-sm text-muted-foreground italic text-center py-8">
                No chat history available
            </p>
        );
    }

    return (
        <div className="space-y-2">
            {messages.slice(0, 150).map((msg, i) => (
                <div
                    key={i}
                    className={cn(
                        "px-3 py-2 rounded-2xl text-xs leading-relaxed",
                        msg.role === "human"
                            ? "ml-auto bg-primary/20 text-foreground/90 rounded-br-sm w-fit max-w-[85%]"
                            : "mr-auto bg-card border border-border/50 text-foreground/80 rounded-bl-sm w-fit max-w-[85%]"
                    )}
                >
                    {msg.content}
                </div>
            ))}
            {messages.length > 150 && (
                <p className="text-xs text-muted-foreground text-center py-2">
                    + {messages.length - 150} more
                </p>
            )}
        </div>
    );
}

function PersonaView({ content }: { content: string }) {
    if (!content) {
        return (
            <p className="text-sm text-muted-foreground italic text-center py-8">
                No user persona available
            </p>
        );
    }

    const renderMarkdown = (text: string) => {
        return text.split("\n").map((line, i) => {
            const trimmed = line.trim();
            if (trimmed.startsWith("# ")) {
                return <h1 key={i} className="text-lg font-bold text-foreground mb-3 mt-4 first:mt-0">{trimmed.slice(2)}</h1>;
            }
            if (trimmed.startsWith("## ")) {
                return <h2 key={i} className="text-sm font-semibold text-foreground/90 mb-2 mt-3">{trimmed.slice(3)}</h2>;
            }
            if (trimmed === "---") {
                return <hr key={i} className="border-border/50 my-4" />;
            }
            if (trimmed.startsWith("**") && trimmed.includes("**")) {
                const boldMatch = trimmed.match(/\*\*(.+?)\*\*/);
                if (boldMatch) {
                    return <p key={i} className="text-xs text-foreground/90 mb-1"><strong className="font-semibold">{boldMatch[1]}</strong>{trimmed.slice(boldMatch[0].length)}</p>;
                }
            }
            if (trimmed.startsWith("- ")) {
                return <li key={i} className="text-xs text-foreground/80 ml-4 mb-1 list-disc">{trimmed.slice(2)}</li>;
            }
            if (!trimmed) return <div key={i} className="h-2" />;
            return <p key={i} className="text-xs text-foreground/80 mb-1">{trimmed}</p>;
        });
    };

    return <div className="bg-background/50 border border-border/50 rounded-xl p-4">{renderMarkdown(content)}</div>;
}
