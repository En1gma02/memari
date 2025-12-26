"use client";

import { motion } from "framer-motion";
import { useEffect, useState } from "react";
import { Activity, Zap, Database, Lock, Search, FileText, Cpu, GitBranch, Layers } from "lucide-react";

export function PipelineArchitecture() {
    const [mounted, setMounted] = useState(false);

    useEffect(() => {
        setMounted(true);
    }, []);

    const indexNodes = [
        { title: "Session", footer: "30m Buffer", icon: Activity, latency: "12ms" },
        { title: "Rewriting", footer: "Llama 3.1 8B", icon: FileText, latency: "450ms" },
        { title: "Persona", footer: "Llama 3.1 8B", icon: UserIcon, latency: "320ms" },
        { title: "Embedding", footer: "MiniLM-L6-v2", icon: Layers, latency: "85ms" },
        { title: "Vector DB", footer: "FAISS + BM25", icon: Database, latency: null },
    ];

    const inferenceNodes = [
        { title: "Safety", footer: "Llama Guard 4", icon: Lock, latency: "15ms" },
        { title: "Tool Plan", footer: "GPT-OSS 120B", icon: Cpu, latency: "800ms" },
        { title: "Fusion", footer: "Llama 3.1 8B", icon: GitBranch, latency: "250ms" },
        { title: "Rerank", footer: "MiniLM-L6-v2", icon: Search, latency: "120ms" },
        { title: "Generate", footer: "GPT-OSS 120B", icon: Zap, latency: null },
    ];

    return (
        <div className="h-full w-full bg-[#080808] border border-white/10 rounded-xl flex flex-col relative overflow-hidden font-sans group">

            {/* Engineering Frame Corners */}
            <div className="absolute top-0 left-0 w-4 h-4 border-t border-l border-white/30 rounded-tl-sm pointer-events-none" />
            <div className="absolute top-0 right-0 w-4 h-4 border-t border-r border-white/30 rounded-tr-sm pointer-events-none" />
            <div className="absolute bottom-0 left-0 w-4 h-4 border-b border-l border-white/30 rounded-bl-sm pointer-events-none" />
            <div className="absolute bottom-0 right-0 w-4 h-4 border-b border-r border-white/30 rounded-br-sm pointer-events-none" />

            {/* Tight Dot Matrix Background */}
            <div className="absolute inset-0 opacity-[0.05] pointer-events-none"
                style={{
                    backgroundImage: 'radial-gradient(circle, #fff 1px, transparent 1px)',
                    backgroundSize: '12px 12px'
                }}
            />

            {/* 1. WRITE PIPELINE (INDEXING) - Compact Zone */}
            <div className="flex-1 flex flex-col justify-end pb-3 pl-4 pr-4 border-t-2 border-t-cyan-500/10 relative">
                <div className="absolute top-2 left-4 flex items-center gap-2">
                    <span className="relative flex h-1.5 w-1.5">
                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75"></span>
                        <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-cyan-500"></span>
                    </span>
                    <h3 className="text-[10px] font-bold text-cyan-500/80 tracking-widest uppercase font-mono">
                        WRITE :: INDEXING
                    </h3>
                </div>

                <div className="flex items-center justify-between gap-2 mt-4">
                    {indexNodes.map((node, i) => (
                        <div key={i} className="flex items-center flex-1 min-w-0 last:flex-none last:w-auto">
                            <PipelineNode node={node} color="cyan" />
                            {/* Connector & Latency */}
                            {i < indexNodes.length - 1 && (
                                <div className="flex-1 px-1 relative flex flex-col items-center justify-center -mt-px">
                                    <span className="text-[8px] font-mono text-cyan-500/50 mb-0.5">{node.latency}</span>
                                    <div className="w-full h-[2px] bg-cyan-900/30 relative overflow-hidden rounded-full">
                                        <DataPacket speed={6} color="bg-cyan-400" delay={i * 1.5} />
                                    </div>
                                </div>
                            )}
                        </div>
                    ))}
                </div>
            </div>

            {/* LATENCY BARRIER - Snug Fit */}
            <div className="shrink-0 h-8 flex items-center justify-center relative">
                <div className="absolute inset-x-4 top-1/2 -translate-y-1/2 h-px border-t border-dashed border-white/10" />
                <span className="bg-[#080808] px-2 py-0.5 text-[8px] font-mono text-white/20 tracking-[0.2em] border border-white/5 rounded-full z-10 uppercase">
                    Latency_Barrier
                </span>
            </div>

            {/* 2. READ PIPELINE (INFERENCE) - Compact Zone */}
            <div className="flex-1 flex flex-col justify-start pt-3 pl-4 pr-4 border-b-2 border-b-emerald-500/10 relative">
                <div className="absolute bottom-2 left-4 flex items-center gap-2">
                    <span className="relative flex h-1.5 w-1.5">
                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                        <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-emerald-500"></span>
                    </span>
                    <h3 className="text-[10px] font-bold text-emerald-500/80 tracking-widest uppercase font-mono">
                        READ :: INFERENCE
                    </h3>
                </div>

                <div className="flex items-center justify-between gap-2 mb-4">
                    {inferenceNodes.map((node, i) => (
                        <div key={i} className="flex items-center flex-1 min-w-0 last:flex-none last:w-auto">
                            <PipelineNode node={node} color="emerald" />
                            {/* Connector & Latency */}
                            {i < inferenceNodes.length - 1 && (
                                <div className="flex-1 px-1 relative flex flex-col items-center justify-center -mt-px">
                                    <span className="text-[8px] font-mono text-emerald-500/50 mb-0.5">{node.latency}</span>
                                    <div className="w-full h-[2px] bg-emerald-900/30 relative overflow-hidden rounded-full">
                                        <DataPacket speed={2} color="bg-emerald-400" delay={i * 0.4} />
                                    </div>
                                </div>
                            )}
                        </div>
                    ))}
                </div>
            </div>

        </div>
    );
}

function PipelineNode({ node, color }: { node: any, color: "cyan" | "emerald" }) {
    const theme = {
        cyan: {
            border: "group-hover:border-cyan-500/30",
            icon: "text-cyan-400",
            glow: "group-hover:shadow-[0_0_15px_rgba(6,182,212,0.1)]",
            pill: "bg-cyan-500/5 text-cyan-300/70 border-cyan-500/10",
            status: "bg-cyan-500"
        },
        emerald: {
            border: "group-hover:border-emerald-500/30",
            icon: "text-emerald-400",
            glow: "group-hover:shadow-[0_0_15px_rgba(16,185,129,0.1)]",
            pill: "bg-emerald-500/5 text-emerald-300/70 border-emerald-500/10",
            status: "bg-emerald-500"
        }
    }[color];

    return (
        <div className={`relative group w-[100px] h-16 bg-[#111] border border-white/5 rounded flex flex-col items-center justify-center gap-1 transition-all duration-300 z-10 cursor-pointer ${theme.border} ${theme.glow}`}>
            {/* Status Blink Light */}
            <div className="absolute top-1.5 right-1.5 w-1 h-1 rounded-full bg-black border border-white/10 overflow-hidden">
                <div className={`w-full h-full ${theme.status} animate-pulse`} />
            </div>

            <div className={`p-1 rounded bg-white/5 ${theme.icon}`}>
                <node.icon className="w-3 h-3" />
            </div>

            <div className="flex flex-col items-center gap-0.5 w-full px-1">
                <span className="text-[9px] font-bold text-white/90 tracking-wide truncate max-w-full">
                    {node.title}
                </span>
                <div className={`px-1.5 py-[1px] rounded-[3px] border text-[8px] font-mono truncate max-w-full ${theme.pill}`}>
                    {node.footer}
                </div>
            </div>
        </div>
    );
}

function DataPacket({ speed, color, delay }: { speed: number, color: string, delay: number }) {
    return (
        <motion.div
            className={`absolute top-0 bottom-0 w-8 z-0 blur-[3px] opacity-80 ${color}`}
            initial={{ left: "-20%" }}
            animate={{ left: "120%" }}
            transition={{
                duration: speed,
                repeat: Infinity,
                ease: "linear",
                delay: delay,
                repeatDelay: 0.5
            }}
        />
    );
}

// User Icon Helper
function UserIcon(props: any) {
    return (
        <svg
            {...props}
            xmlns="http://www.w3.org/2000/svg"
            width="24"
            height="24"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
        >
            <path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2" />
            <circle cx="12" cy="7" r="4" />
        </svg>
    )
}
