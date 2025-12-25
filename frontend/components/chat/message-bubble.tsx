"use client";

import { cn } from "@/lib/utils";
import { Check, CheckCheck } from "lucide-react";

interface MessageBubbleProps {
    content: string;
    role: "user" | "assistant";
    timestamp?: Date;
    status?: "sending" | "sent" | "delivered";
    index?: number;
}

export function MessageBubble({
    content,
    role,
    timestamp,
    status = "delivered",
    index = 0,
}: MessageBubbleProps) {
    const isUser = role === "user";
    const time = timestamp
        ? timestamp.toLocaleTimeString("en-US", {
            hour: "2-digit",
            minute: "2-digit",
            hour12: false,
        })
        : new Date().toLocaleTimeString("en-US", {
            hour: "2-digit",
            minute: "2-digit",
            hour12: false,
        });

    return (
        <div
            className={cn(
                "inline-flex flex-col gap-1 px-3 py-2 rounded-2xl animate-in fade-in slide-in-from-bottom-2",
                "transition-all duration-200",
                isUser
                    ? "ml-auto bg-primary text-primary-foreground rounded-br-sm max-w-[75%]"
                    : "mr-auto bg-card/80 backdrop-blur-sm border border-border/50 rounded-bl-sm max-w-[75%]"
            )}
            style={{
                animationDelay: `${index * 50}ms`,
                animationFillMode: "backwards",
            }}
        >
            <p className="text-sm leading-relaxed whitespace-pre-wrap overflow-wrap-break-word">
                {content}
            </p>
            <div
                className={cn(
                    "flex items-center gap-1 self-end",
                    isUser ? "text-primary-foreground/70" : "text-muted-foreground"
                )}
            >
                <span className="text-[10px]">{time}</span>
                {isUser && (
                    <>
                        {status === "sending" && (
                            <Check className="w-3 h-3 text-white/50" />
                        )}
                        {status === "sent" && <Check className="w-3 h-3 text-white/80" />}
                        {status === "delivered" && (
                            <CheckCheck className="w-3 h-3 text-[#1e3a5f]" />
                        )}
                    </>
                )}
            </div>
        </div>
    );
}

/**
 * Typing indicator component - animated dots
 */
export function TypingIndicator() {
    return (
        <div className="inline-flex items-center gap-1 px-4 py-3 bg-card/80 backdrop-blur-sm border border-border/50 rounded-2xl rounded-bl-sm">
            <div className="flex items-center gap-1">
                <span
                    className="w-2 h-2 bg-muted-foreground/60 rounded-full animate-bounce"
                    style={{ animationDelay: "0ms" }}
                />
                <span
                    className="w-2 h-2 bg-muted-foreground/60 rounded-full animate-bounce"
                    style={{ animationDelay: "150ms" }}
                />
                <span
                    className="w-2 h-2 bg-muted-foreground/60 rounded-full animate-bounce"
                    style={{ animationDelay: "300ms" }}
                />
            </div>
        </div>
    );
}

/**
 * Date separator component
 */
export function DateSeparator({ date }: { date: Date }) {
    const today = new Date();
    const isToday = date.toDateString() === today.toDateString();

    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);
    const isYesterday = date.toDateString() === yesterday.toDateString();

    let label = date.toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
        year: "numeric",
    });

    if (isToday) label = "Today";
    else if (isYesterday) label = "Yesterday";

    return (
        <div className="flex items-center justify-center my-4">
            <span className="px-3 py-1 text-xs text-muted-foreground bg-card/50 rounded-full border border-border/30">
                {label}
            </span>
        </div>
    );
}
