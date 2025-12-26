"use client";

import { useState, useEffect } from "react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { cn } from "@/lib/utils";
import { fetchChatHistory, fetchUserPersona, fetchAriLifeContent, parseChatHistory, ChatMessage } from "@/lib/data";
import ReactMarkdown from 'react-markdown';
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";
import { User, History, BookOpen } from "lucide-react";

type ViewMode = "history" | "persona" | "ari-life";

// View descriptions
const VIEW_DESCRIPTIONS: Record<ViewMode, string> = {
    history: "Chat database used for long term memory. Updated after every chat session.",
    persona: "User's stored preferences, personality traits, and facts. Updated after every session. Fully Passed when get_user_persona tool is called.",
    "ari-life": "Information about Ari's life. Undergoes RAG pipeline when 'get_self_info' tool is called."
};

// Database metadata
const DB_METADATA = {
    history: {
        totalChats: 750,
        totalSessions: 93,
        totalTokens: 29645,
        embeddedTokens: 13255,
        label1: "Sessions",
        label2: "Messages",
        label3: "Tokens",
        label4: "Embedded",
        val1: "93",
        val2: "750",
        val3: "29,645",
        val4: "13,255"
    },
    persona: {
        val1: "2,450",
        val2: "15,800",
        label1: "Tokens",
        label2: "Characters",
    },
    "ari-life": {
        val1: "334",
        val2: "138,908",
        label1: "Chunks",
        label2: "Tokens",
    }
};

export function ChatHistory() {
    const [viewMode, setViewMode] = useState<ViewMode>("history");
    const [historyMessages, setHistoryMessages] = useState<ChatMessage[]>([]);
    const [personaContent, setPersonaContent] = useState("");
    const [ariLifeContent, setAriLifeContent] = useState("");
    const [isLoading, setIsLoading] = useState(false);

    useEffect(() => {
        loadData();
    }, [viewMode]);

    const loadData = async () => {
        setIsLoading(true);
        try {
            if (viewMode === "history" && historyMessages.length === 0) {
                const content = await fetchChatHistory();
                const messages = parseChatHistory(content);
                setHistoryMessages(messages);
            } else if (viewMode === "persona" && !personaContent) {
                const content = await fetchUserPersona();
                setPersonaContent(content);
            } else if (viewMode === "ari-life" && !ariLifeContent) {
                const content = await fetchAriLifeContent();
                setAriLifeContent(content);
            }
        } finally {
            setIsLoading(false);
        }
    };

    const renderFooter = () => {
        if (viewMode === "history") {
            const stats = DB_METADATA.history;
            return (
                <div className="w-full grid grid-cols-2 gap-x-4 gap-y-0.5">
                    <div className="text-left">
                        <p className="text-xs font-semibold text-foreground">{stats.val1}</p>
                        <p className="text-[8px] text-muted-foreground uppercase tracking-wide">{stats.label1}</p>
                    </div>
                    <div className="text-left">
                        <p className="text-xs font-semibold text-foreground">{stats.val2}</p>
                        <p className="text-[8px] text-muted-foreground uppercase tracking-wide">{stats.label2}</p>
                    </div>
                    <div className="text-left">
                        <p className="text-xs font-semibold text-foreground">{stats.val3}</p>
                        <p className="text-[8px] text-muted-foreground uppercase tracking-wide">{stats.label3}</p>
                    </div>
                    <div className="text-left">
                        <p className="text-xs font-semibold text-primary">{stats.val4}</p>
                        <p className="text-[8px] text-muted-foreground uppercase tracking-wide">{stats.label4}</p>
                    </div>
                </div>
            );
        }

        const stats = DB_METADATA[viewMode];
        return (
            <div className="w-full flexflex-col gap-1">
                <div className="grid grid-cols-2 gap-x-4 mb-2">
                    <div className="text-left">
                        <p className="text-xs font-semibold text-foreground">{stats.val1}</p>
                        <p className="text-[8px] text-muted-foreground uppercase tracking-wide">{stats.label1}</p>
                    </div>
                    <div className="text-left">
                        <p className="text-xs font-semibold text-foreground">{stats.val2}</p>
                        <p className="text-[8px] text-muted-foreground uppercase tracking-wide">{stats.label2}</p>
                    </div>
                </div>
            </div>
        );
    };

    return (
        <div className="h-screen flex flex-col bg-card/30 backdrop-blur-sm border-r border-border/50">
            {/* Header - Dropdown */}
            <div className="px-4 pt-4 pb-2 border-b border-border/50 shrink-0">
                <Select value={viewMode} onValueChange={(v) => setViewMode(v as ViewMode)}>
                    <SelectTrigger className="w-full bg-background/50 border-border/50 h-auto py-2">
                        {/* Custom Trigger Content - Clean Title Only */}
                        <div className="flex items-center gap-2 text-foreground">
                            {viewMode === "history" && <History className="w-4 h-4 text-muted-foreground" />}
                            {viewMode === "persona" && <User className="w-4 h-4 text-muted-foreground" />}
                            {viewMode === "ari-life" && <BookOpen className="w-4 h-4 text-muted-foreground" />}
                            <span className="text-sm font-medium">
                                {viewMode === "history" && "Chat History"}
                                {viewMode === "persona" && "User Persona"}
                                {viewMode === "ari-life" && "Ari's Life"}
                            </span>
                        </div>
                    </SelectTrigger>
                    <SelectContent>
                        <SelectItem value="history">
                            <div className="flex flex-col gap-1 py-1">
                                <div className="flex items-center gap-2">
                                    <History className="w-4 h-4 text-muted-foreground" />
                                    <span className="font-medium">Chat History</span>
                                </div>
                                <span className="text-[10px] text-muted-foreground pl-6 leading-relaxed whitespace-normal">
                                    Chat database used for long term memory. Updated after every chat session.
                                </span>
                            </div>
                        </SelectItem>
                        <SelectItem value="persona">
                            <div className="flex flex-col gap-1 py-1">
                                <div className="flex items-center gap-2">
                                    <User className="w-4 h-4 text-muted-foreground" />
                                    <span className="font-medium">User Persona</span>
                                </div>
                                <span className="text-[10px] text-muted-foreground pl-6 leading-relaxed whitespace-normal">
                                    User's stored preferences, personality traits, and facts. Updated after every session. Fully Passed when get_user_persona tool is called.
                                </span>
                            </div>
                        </SelectItem>
                        <SelectItem value="ari-life">
                            <div className="flex flex-col gap-1 py-1">
                                <div className="flex items-center gap-2">
                                    <BookOpen className="w-4 h-4 text-muted-foreground" />
                                    <span className="font-medium">Ari's Life</span>
                                </div>
                                <span className="text-[10px] text-muted-foreground pl-6 leading-relaxed whitespace-normal">
                                    Information about Ari's life. Undergoes RAG pipeline when 'get_self_info' tool is called.
                                </span>
                            </div>
                        </SelectItem>
                    </SelectContent>
                </Select>

                {/* Description Text Below Dropdown */}
                <p className="text-[10px] text-muted-foreground leading-relaxed mt-2 px-1">
                    {VIEW_DESCRIPTIONS[viewMode]}
                </p>
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
                        ) : viewMode === "persona" ? (
                            <MarkdownView content={personaContent} />
                        ) : (
                            <MarkdownView content={ariLifeContent} />
                        )}
                    </div>
                </ScrollArea>
            </div>

            {/* Footer */}
            <div className="h-[72px] px-4 flex items-center shrink-0 bg-background/30">
                {renderFooter()}
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

function MarkdownView({ content }: { content: string }) {
    if (!content) {
        return (
            <p className="text-sm text-muted-foreground italic text-center py-8">
                No content available
            </p>
        );
    }

    return (
        <div className="bg-background/50 border border-border/50 rounded-xl p-4 prose prose-invert prose-xs max-w-none">
            <ReactMarkdown
                components={{
                    h1: ({ node, ...props }) => <h1 className="text-lg font-bold text-foreground mb-3 mt-4 first:mt-0" {...props} />,
                    h2: ({ node, ...props }) => <h2 className="text-sm font-semibold text-foreground/90 mb-2 mt-3" {...props} />,
                    h3: ({ node, ...props }) => <h3 className="text-xs font-semibold text-foreground/90 mb-1 mt-2" {...props} />,
                    p: ({ node, ...props }) => <p className="text-xs text-foreground/80 mb-2 leading-relaxed" {...props} />,
                    ul: ({ node, ...props }) => <ul className="list-disc ml-4 mb-2 space-y-1" {...props} />,
                    li: ({ node, ...props }) => <li className="text-xs text-foreground/80" {...props} />,
                    hr: ({ node, ...props }) => <hr className="border-border/50 my-4" {...props} />,
                    blockquote: ({ node, ...props }) => <blockquote className="border-l-2 border-primary/50 pl-3 italic text-muted-foreground my-2" {...props} />,
                    strong: ({ node, ...props }) => <strong className="font-semibold text-primary/90" {...props} />,
                }}
            >
                {content}
            </ReactMarkdown>
        </div>
    );
}
