"use client";

import { useRef, useEffect, KeyboardEvent } from "react";
import Image from "next/image";
import { Send, Github, Eraser } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { MessageBubble, TypingIndicator, DateSeparator } from "./message-bubble";
import { cn } from "@/lib/utils";

interface Message {
    id: string;
    role: "user" | "assistant";
    content: string[];
    timestamp: Date;
    status?: "sending" | "sent" | "delivered";
}

interface ChatInterfaceProps {
    messages: Message[];
    onSendMessage: (message: string) => void;
    onClearChat: () => void;
    isLoading?: boolean;
    isOnline?: boolean;
}

export function ChatInterface({
    messages,
    onSendMessage,
    onClearChat,
    isLoading = false,
    isOnline = true,
}: ChatInterfaceProps) {
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const textareaRef = useRef<HTMLTextAreaElement>(null);

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages, isLoading]);

    const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    const handleSend = () => {
        const textarea = textareaRef.current;
        if (!textarea) return;
        const message = textarea.value.trim();
        if (message && !isLoading) {
            onSendMessage(message);
            textarea.value = "";
            textarea.style.height = "auto";
        }
    };

    const handleInput = () => {
        const textarea = textareaRef.current;
        if (textarea) {
            textarea.style.height = "auto";
            textarea.style.height = Math.min(textarea.scrollHeight, 120) + "px";
        }
    };

    const getDateKey = (date: Date) => date.toDateString();

    return (
        <div className="h-screen flex flex-col bg-background border-x border-border/30">
            {/* Header - Larger */}
            <div className="h-[72px] px-6 flex items-center justify-between border-b border-border/50 bg-card/30 backdrop-blur-sm shrink-0">
                <div className="flex items-center gap-4">
                    {/* Profile Picture - Larger, proper circle */}
                    <div className="relative">
                        <div className="w-12 h-12 rounded-full overflow-hidden ring-2 ring-border/50">
                            <Image
                                src="/ari_profile.png"
                                alt="Ari"
                                width={48}
                                height={48}
                                className="object-cover w-full h-full"
                            />
                        </div>
                        <div
                            className={cn(
                                "absolute bottom-0 right-0 w-3.5 h-3.5 rounded-full border-2 border-card",
                                isOnline ? "bg-green-500" : "bg-gray-400"
                            )}
                        />
                    </div>

                    {/* Name and Status - Larger */}
                    <div>
                        <h1 className="text-lg font-semibold text-foreground">Ari</h1>
                        <p className="text-sm text-muted-foreground">
                            {isOnline ? "Online" : "Offline"}
                        </p>
                    </div>
                </div>

                {/* Right Side Icons - Larger */}
                <div className="flex items-center gap-2">
                    <a
                        href="https://github.com/En1gma02/memari"
                        target="_blank"
                        rel="noopener noreferrer"
                        className="h-10 w-10 inline-flex items-center justify-center rounded-xl text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
                    >
                        <Github className="w-5 h-5" />
                    </a>
                    <Button
                        variant="ghost"
                        size="icon"
                        onClick={onClearChat}
                        className="h-10 w-10 rounded-xl text-muted-foreground hover:text-foreground"
                        title="Clear chat"
                    >
                        <Eraser className="w-5 h-5" />
                    </Button>
                </div>
            </div>

            {/* Messages - Fixed height with proper scroll */}
            <div className="flex-1 min-h-0 overflow-hidden">
                <ScrollArea className="h-full">
                    <div className="px-6 py-4">
                        {messages.length === 0 ? (
                            <div className="h-full min-h-[60vh] flex flex-col items-center justify-center text-center">
                                <div className="w-20 h-20 rounded-full bg-primary/10 flex items-center justify-center mb-4 overflow-hidden ring-2 ring-primary/20">
                                    <Image
                                        src="/ari_profile.png"
                                        alt="Ari"
                                        width={80}
                                        height={80}
                                        className="object-cover w-full h-full"
                                    />
                                </div>
                                <h3 className="text-xl font-medium text-foreground/90 mb-2">
                                    Start a conversation
                                </h3>
                                <p className="text-sm text-muted-foreground max-w-sm">
                                    Ask Ari anything. Memories from past conversations help provide personalized responses.
                                </p>
                            </div>
                        ) : (
                            <div className="space-y-4">
                                {messages.map((message, msgIndex) => {
                                    const prevMessage = messages[msgIndex - 1];
                                    const showDateSeparator =
                                        msgIndex === 0 ||
                                        (prevMessage && getDateKey(message.timestamp) !== getDateKey(prevMessage.timestamp));

                                    return (
                                        <div key={message.id}>
                                            {showDateSeparator && <DateSeparator date={message.timestamp} />}
                                            <div className={cn("flex flex-col gap-1", message.role === "user" ? "items-end" : "items-start")}>
                                                {message.content.map((bubble, bubbleIndex) => (
                                                    <MessageBubble
                                                        key={`${message.id}-${bubbleIndex}`}
                                                        content={bubble}
                                                        role={message.role}
                                                        timestamp={message.timestamp}
                                                        status={message.status}
                                                        index={bubbleIndex}
                                                    />
                                                ))}
                                            </div>
                                        </div>
                                    );
                                })}
                                {isLoading && (
                                    <div className="pt-2 flex">
                                        <TypingIndicator />
                                    </div>
                                )}
                                <div ref={messagesEndRef} />
                            </div>
                        )}
                    </div>
                </ScrollArea>
            </div>

            {/* Input - Footer */}
            <div className="h-[72px] px-6 flex items-center border-t border-border/50 bg-card/30 backdrop-blur-sm shrink-0">
                <div className="flex gap-3 items-center w-full">
                    <textarea
                        ref={textareaRef}
                        placeholder="Type a message..."
                        onKeyDown={handleKeyDown}
                        onInput={handleInput}
                        disabled={isLoading}
                        rows={1}
                        className={cn(
                            "flex-1 resize-none bg-background/50 border border-border/50 rounded-xl px-4 py-2.5",
                            "text-sm placeholder:text-muted-foreground/60",
                            "focus:outline-none focus:border-primary/50 focus:ring-1 focus:ring-primary/20",
                            "disabled:opacity-50 disabled:cursor-not-allowed",
                            "h-[44px]"
                        )}
                    />
                    <Button
                        onClick={handleSend}
                        disabled={isLoading}
                        size="icon"
                        className="h-[44px] w-[44px] shrink-0 rounded-xl"
                    >
                        <Send className="w-5 h-5" />
                    </Button>
                </div>
            </div>
        </div>
    );
}
