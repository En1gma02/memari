"use client";

import { Wrench, Database, ChevronDown, Sparkles, User, Search, BookOpen } from "lucide-react";
import { cn } from "@/lib/utils";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useState } from "react";

export interface ContextChunk {
    text: string;
    score?: number;
}

interface DebugInfo {
    toolsCalled: string[];
    contextChunks: ContextChunk[];
}

interface DebugPanelProps {
    debugInfo: DebugInfo;
    sessionId: string;
}

// Available tools with descriptions
const AVAILABLE_TOOLS = [
    {
        name: "get_user_persona",
        icon: User,
        description: "Retrieves user's stored preferences, personality traits, and facts",
    },
    {
        name: "get_long_term_memory",
        icon: Search,
        description: "Semantic search through indexed conversation history using hybrid RAG",
    },
    {
        name: "get_self_info",
        icon: BookOpen,
        description: "Retrieves information about Ari's life story, background, and personality",
    },
];

export function DebugPanel({ debugInfo, sessionId }: DebugPanelProps) {
    return (
        <div className="h-screen flex flex-col bg-card/30 backdrop-blur-sm border-l border-border/50">
            {/* Header - Matching height */}
            <div className="h-[72px] px-4 flex items-center border-b border-border/50 shrink-0">
                <div>
                    <h2 className="text-lg font-semibold text-foreground">Memory Panel</h2>
                    <p className="text-xs text-muted-foreground font-mono truncate max-w-[200px]">
                        {sessionId}
                    </p>
                </div>
            </div>

            {/* Scrollable Content */}
            <div className="flex-1 min-h-0 overflow-hidden">
                <ScrollArea className="h-full">
                    <div className="p-4 space-y-6">
                        {/* Available Tools Section */}
                        <section>
                            <div className="flex items-center gap-2 mb-3">
                                <Sparkles className="w-4 h-4 text-primary" />
                                <span className="text-xs font-semibold text-foreground uppercase tracking-wider">
                                    Available Tools
                                </span>
                            </div>
                            <div className="space-y-2">
                                {AVAILABLE_TOOLS.map((tool) => {
                                    const Icon = tool.icon;
                                    return (
                                        <div
                                            key={tool.name}
                                            className="bg-background/30 border border-border/30 rounded-xl p-3"
                                        >
                                            <div className="flex items-start gap-3">
                                                <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center shrink-0">
                                                    <Icon className="w-4 h-4 text-primary" />
                                                </div>
                                                <div className="flex-1 min-w-0">
                                                    <p className="text-xs font-mono font-medium text-foreground mb-0.5">
                                                        {tool.name}
                                                    </p>
                                                    <p className="text-[11px] text-muted-foreground leading-relaxed">
                                                        {tool.description}
                                                    </p>
                                                </div>
                                            </div>
                                        </div>
                                    );
                                })}
                            </div>
                        </section>

                        {/* Tools Used Section */}
                        <section>
                            <div className="flex items-center gap-2 mb-3">
                                <Wrench className="w-4 h-4 text-primary" />
                                <span className="text-xs font-semibold text-foreground uppercase tracking-wider">
                                    Tools Used
                                </span>
                            </div>
                            {debugInfo.toolsCalled.length > 0 ? (
                                <div className="space-y-2">
                                    {debugInfo.toolsCalled.map((tool, i) => (
                                        <div
                                            key={i}
                                            className="flex items-center gap-2 px-3 py-2 bg-green-500/10 border border-green-500/20 rounded-xl"
                                        >
                                            <div className="w-2 h-2 rounded-full bg-green-500" />
                                            <span className="text-xs font-mono text-foreground/90">{tool}</span>
                                        </div>
                                    ))}
                                </div>
                            ) : (
                                <p className="text-xs text-muted-foreground italic px-1">No tools called yet</p>
                            )}
                        </section>

                        {/* Context Chunks Section */}
                        <section>
                            <div className="flex items-center gap-2 mb-3">
                                <Database className="w-4 h-4 text-primary" />
                                <span className="text-xs font-semibold text-foreground uppercase tracking-wider">
                                    Retrieved Context
                                </span>
                            </div>
                            {debugInfo.contextChunks.length > 0 ? (
                                <div className="space-y-2">
                                    {debugInfo.contextChunks.map((chunk, i) => (
                                        <ContextChunkItem key={i} chunk={chunk} index={i} />
                                    ))}
                                </div>
                            ) : (
                                <p className="text-xs text-muted-foreground italic px-1">No context retrieved</p>
                            )}
                        </section>
                    </div>
                </ScrollArea>
            </div>

            {/* Footer - Matching height */}
            <div className="h-[72px] px-4 flex items-center justify-center border-t border-border/50 shrink-0">
                <p className="text-[10px] text-muted-foreground text-center leading-relaxed">
                    <span className="text-foreground/70">Rephrased Fusion Retrieval</span>
                    <br />
                    Hybrid RAG: 75% Cosine + 25% BM25
                    <br />
                    <span className="text-primary">CrossEncoder Re-ranking</span>
                    <br />
                </p>
            </div>
        </div>
    );
}

function ContextChunkItem({ chunk, index }: { chunk: ContextChunk; index: number }) {
    const [isExpanded, setIsExpanded] = useState(false);

    return (
        <div className="bg-background/50 border border-border/50 rounded-xl overflow-hidden">
            <button
                onClick={() => setIsExpanded(!isExpanded)}
                className="w-full flex items-center justify-between px-3 py-2.5 hover:bg-background/80 transition-colors"
            >
                <span className="text-xs font-medium text-foreground/80">
                    Chunk {index + 1}
                    {chunk.score !== undefined && (
                        <span className="ml-2 text-primary">
                            {(chunk.score * 100).toFixed(0)}%
                        </span>
                    )}
                </span>
                <ChevronDown
                    className={cn(
                        "w-4 h-4 text-muted-foreground transition-transform",
                        isExpanded && "rotate-180"
                    )}
                />
            </button>
            {isExpanded && (
                <div className="px-3 pb-3 border-t border-border/30">
                    <p className="text-xs font-mono text-foreground/70 whitespace-pre-wrap leading-relaxed pt-2">
                        {chunk.text}
                    </p>
                </div>
            )}
        </div>
    );
}
