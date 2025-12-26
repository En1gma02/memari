"use client";

import { motion } from "framer-motion";
import { User, Database, Fingerprint, ArrowRight, Terminal } from "lucide-react";

export function ToolRegistry() {
    const tools = [
        {
            funcName: "get_user_persona",
            args: "()",
            desc: "Retrieves user's stored preferences & traits.",
            icon: User,
            color: "text-blue-400",
            borderColor: "border-l-blue-400",
            bgHover: "group-hover:bg-blue-500/10",
            borderHover: "group-hover:border-blue-400/50"
        },
        {
            funcName: "get_long_term_memory",
            args: "(query)",
            desc: "Hybrid RAG search on chat history.",
            icon: Database,
            color: "text-emerald-400",
            borderColor: "border-l-emerald-400",
            bgHover: "group-hover:bg-emerald-500/10",
            borderHover: "group-hover:border-emerald-400/50"
        },
        {
            funcName: "get_self_info",
            args: "()",
            desc: "Access to Ari's static life bio (334 chunks).",
            icon: Fingerprint,
            color: "text-purple-400",
            borderColor: "border-l-purple-400",
            bgHover: "group-hover:bg-purple-500/10",
            borderHover: "group-hover:border-purple-400/50"
        }
    ];

    return (
        <div className="h-full w-full bg-[#050505] border border-white/10 rounded-3xl p-5 flex flex-col relative overflow-hidden">

            {/* Header */}
            <div className="flex items-center justify-between mb-4 z-10 border-b border-white/5 pb-2">
                <div className="flex items-center gap-2">
                    <Terminal className="w-3.5 h-3.5 text-white/40" />
                    <span className="text-[10px] uppercase font-mono tracking-widest text-white/40">AVAILABLE_TOOLS</span>
                </div>
                <div className="px-1.5 py-0.5 rounded bg-emerald-500/10 border border-emerald-500/20">
                    <span className="text-[9px] font-mono text-emerald-400">3 Active</span>
                </div>
            </div>

            {/* Tool List */}
            <div className="flex-1 h-full flex flex-col justify-between z-10 min-h-0">
                {tools.map((tool, i) => (
                    <motion.div
                        key={tool.funcName}
                        initial={{ opacity: 0, x: -10 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: i * 0.1 }}
                        className={`group relative flex items-center gap-3 p-3 rounded-lg bg-[#0A0A0A] border border-white/5 border-l-2 ${tool.borderColor} hover:border-l-4 transition-all duration-300 cursor-pointer ${tool.borderHover}`}
                    >
                        {/* Hover Glow Background */}
                        <div className={`absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-300 ${tool.bgHover}`} />

                        {/* Icon Container */}
                        <div className="relative flex-none w-8 h-8 rounded-md bg-white/5 flex items-center justify-center border border-white/5 group-hover:border-white/20 transition-colors">
                            <tool.icon className={`w-4 h-4 ${tool.color}`} />
                        </div>

                        {/* Content */}
                        <div className="flex-1 min-w-0 relative flex flex-col justify-center gap-0.5">
                            <div className="font-mono text-[11px] font-medium leading-tight whitespace-normal break-words">
                                <span className={tool.color}>{tool.funcName}</span>
                                <span className="text-white/30">{tool.args}</span>
                            </div>
                            <p className="text-[10px] text-white/40 font-light leading-snug whitespace-normal">
                                {tool.desc}
                            </p>
                        </div>

                        {/* Arrow Action */}
                        <div className="relative flex-none w-5 h-5 flex items-center justify-center opacity-0 group-hover:opacity-100 -translate-x-2 group-hover:translate-x-0 transition-all duration-300">
                            <ArrowRight className={`w-3.5 h-3.5 ${tool.color}`} />
                        </div>
                    </motion.div>
                ))}
            </div>

        </div>
    );
}
