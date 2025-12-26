"use client";

import { motion } from "framer-motion";
import { Cpu, Database, User, Book, HardDrive } from "lucide-react";

export function MemoryLayers() {
    const memoryFiles = [
        {
            name: "active",
            ext: ".buffer",
            icon: Cpu,
            desc: "Sliding Window (Last 10 + Session)",
            stat: "LIVE",
            isLive: true,
            extColor: "text-emerald-400",
            iconColor: "text-emerald-400"
        },
        {
            name: "chat_history",
            ext: ".bin",
            icon: Database,
            desc: "Vectorized Sessions & Recursive Summaries",
            stat: "93 Sessions",
            extColor: "text-white/60",
            iconColor: "text-blue-400"
        },
        {
            name: "user_persona",
            ext: ".md",
            icon: User,
            desc: "Psychological Traits & User Facts",
            stat: "2.4k Tokens",
            extColor: "text-blue-400",
            iconColor: "text-indigo-400"
        },
        {
            name: "ari_life",
            ext: ".bin",
            icon: Book,
            desc: "Static Biography & Narrative Embeddings",
            stat: "138k Tokens",
            extColor: "text-purple-400",
            iconColor: "text-purple-400"
        }
    ];

    return (
        <div className="h-full w-full bg-[#050505] border border-white/10 rounded-3xl p-5 flex flex-col relative overflow-hidden font-sans">

            {/* Background Grid */}
            <div className="absolute inset-0 opacity-[0.03] pointer-events-none"
                style={{
                    backgroundImage: 'linear-gradient(rgba(255, 255, 255, 0.1) 1px, transparent 1px), linear-gradient(90deg, rgba(255, 255, 255, 0.1) 1px, transparent 1px)',
                    backgroundSize: '24px 24px'
                }}
            />

            {/* Header */}
            <div className="flex items-center gap-2 mb-2 z-10 border-b border-white/5 pb-2">
                <HardDrive className="w-3.5 h-3.5 text-white/40" />
                <span className="text-[10px] uppercase font-mono tracking-widest text-white/40">DATA_SCHEMA</span>
            </div>

            {/* File System List */}
            <div className="flex-1 h-full flex flex-col justify-between z-10 min-h-0 relative">

                {/* Tree Line */}
                <div className="absolute left-[15px] top-2 bottom-2 w-px bg-white/5 -z-10" />

                {memoryFiles.map((file, i) => (
                    <motion.div
                        key={file.name}
                        initial={{ opacity: 0, x: -5 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: i * 0.1 }}
                        className="group flex items-center gap-3 py-2.5 px-2 rounded-lg hover:bg-white/[0.02] transition-colors cursor-pointer"
                    >
                        {/* Icon */}
                        <div className={`relative flex-none w-7 h-7 rounded bg-black/40 border border-white/5 group-hover:border-white/20 flex items-center justify-center transition-colors z-10 ${file.iconColor}`}>
                            <file.icon className={`w-3.5 h-3.5 ${file.isLive ? 'animate-pulse' : ''}`} />
                            {file.isLive && (
                                <div className="absolute top-0.5 right-0.5 w-1 h-1 bg-emerald-400 rounded-full animate-ping" />
                            )}
                        </div>

                        {/* File Details */}
                        <div className="flex-1 min-w-0 flex flex-col justify-center gap-0.5">
                            <div className="font-mono text-[11px] leading-none text-white/90 truncate">
                                <span>{file.name}</span>
                                <span className={`${file.extColor}`}>{file.ext}</span>
                            </div>
                            <span className="text-[10px] text-white/40 font-sans leading-tight">
                                {file.desc}
                            </span>
                        </div>

                        {/* Stat/Badge */}
                        <div className="flex-none w-[80px] text-right shrink-0">
                            {file.isLive ? (
                                <span className="inline-flex items-center px-1.5 py-0.5 rounded-full bg-emerald-500/10 text-[9px] font-bold text-emerald-400 border border-emerald-500/20 tracking-wider">
                                    LIVE
                                </span>
                            ) : (
                                <span className="font-mono text-[10px] text-white/50">
                                    {file.stat}
                                </span>
                            )}
                        </div>
                    </motion.div>
                ))}
            </div>

        </div>
    );
}
