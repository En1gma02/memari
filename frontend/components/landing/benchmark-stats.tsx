"use client";

import { motion } from "framer-motion";
import { Activity, Database, Server } from "lucide-react";
import { useEffect, useState } from "react";

export function BenchmarkStats() {
    const [mounted, setMounted] = useState(false);

    useEffect(() => {
        setMounted(true);
    }, []);

    return (
        <div className="h-full w-full bg-[#09090b] border border-white/10 rounded-3xl p-6 flex flex-col relative overflow-hidden font-mono">

            {/* Background Grid Pattern */}
            <div className="absolute inset-0 opacity-[0.03] pointer-events-none"
                style={{
                    backgroundImage: 'linear-gradient(rgba(255,255,255,0.1) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.1) 1px, transparent 1px)',
                    backgroundSize: '20px 20px'
                }}
            />

            {/* Header */}
            <div className="flex items-center gap-3 mb-8 z-10">
                <div className="relative flex items-center justify-center w-3 h-3">
                    <span className="absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75 animate-ping"></span>
                    <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
                </div>
                <span className="text-xs font-bold tracking-widest text-zinc-500 uppercase">
                    BENCHMARKED
                </span>
            </div>

            {/* Main Metrics Area */}
            <div className="flex-1 flex flex-col gap-8 z-10 z-[2]">

                {/* Metric 1: Hit Rate (Segmented Bar) */}
                <div className="space-y-3">
                    <div className="flex justify-between items-end">
                        <span className="text-[10px] uppercase text-zinc-500 tracking-wider">Retrieval Hit Rate</span>
                        <div className="flex items-baseline gap-1">
                            <span className="text-4xl font-bold text-white tracking-tighter">88</span>
                            <span className="text-emerald-400 text-lg">%</span>
                        </div>
                    </div>

                    {/* Segmented Volume Meter */}
                    <div className="flex gap-1 h-3">
                        {[...Array(10)].map((_, i) => (
                            <motion.div
                                key={i}
                                className={`flex-1 rounded-sm ${i < 9 ? 'bg-emerald-500' : 'bg-zinc-800'}`}
                                initial={{ opacity: 0, scaleY: 0 }}
                                animate={{ opacity: mounted ? (i < 9 ? 1 : 0.3) : 0, scaleY: mounted ? 1 : 0 }}
                                transition={{
                                    duration: 0.4,
                                    delay: i * 0.05 + 0.2,
                                    ease: "backOut"
                                }}
                            />
                        ))}
                    </div>
                </div>

                {/* Metric 2: MRR (Score Card) */}
                <div className="space-y-4">
                    <div className="flex flex-col">
                        <span className="text-[10px] uppercase text-zinc-500 tracking-wider mb-1">MRR Score</span>
                        <div className="flex items-baseline justify-between">
                            <span className="text-4xl font-bold text-white tracking-tighter">0.69</span>
                            <span className="text-[10px] text-emerald-400/80 uppercase tracking-widest border border-emerald-500/20 px-2 py-0.5 rounded bg-emerald-500/5">Rank 1 Accuracy</span>
                        </div>
                    </div>

                    {/* Linear Scale */}
                    <div className="relative h-px w-full bg-zinc-800 mt-2">
                        {/* Ticks */}
                        <div className="absolute inset-x-0 -top-1 flex justify-between">
                            {[0, 25, 50, 75, 100].map((tick) => (
                                <div key={tick} className="h-2 w-px bg-zinc-800" />
                            ))}
                        </div>
                        {/* Marker */}
                        <motion.div
                            className="absolute top-1/2 -translate-y-1/2 w-1.5 h-4 bg-emerald-400"
                            initial={{ left: "0%" }}
                            animate={{ left: mounted ? "69%" : "0%" }}
                            transition={{ duration: 1, delay: 0.8, ease: "circOut" }}
                        >
                            <div className="absolute -top-6 left-1/2 -translate-x-1/2 text-[9px] text-emerald-400 font-bold opacity-0 animate-[fadeIn_0.5s_ease-out_1.5s_forwards]">
                                0.69
                            </div>
                        </motion.div>
                        <motion.div
                            className="absolute top-0 left-0 h-full bg-emerald-500/20"
                            initial={{ width: "0%" }}
                            animate={{ width: mounted ? "69%" : "0%" }}
                            transition={{ duration: 1, delay: 0.8, ease: "circOut" }}
                        />
                    </div>
                </div>
            </div>

            {/* Footer: Configuration Box */}
            <div className="mt-auto pt-6 border-t border-dashed border-white/10 z-10">
                <div className="grid grid-cols-2 gap-y-4 gap-x-2">
                    <div className="col-span-2 flex items-center gap-2 mb-1">
                        <Activity className="w-3 h-3 text-zinc-600" />
                        <span className="text-[9px] uppercase text-zinc-600 tracking-widest font-bold">Configuration</span>
                    </div>

                    <div className="space-y-0.5">
                        <span className="text-[10px] text-zinc-500 block">Dataset</span>
                        <span className="text-xs text-zinc-300">65M+ Tokens</span>
                    </div>

                    <div className="space-y-0.5">
                        <span className="text-[10px] text-zinc-500 block">Test Set</span>
                        <span className="text-xs text-zinc-300">N=100 Queries</span>
                    </div>

                    <div className="col-span-2 flex items-center justify-between bg-zinc-900/50 rounded p-2 border border-white/5 mt-1">
                        <div className="flex items-center gap-2">
                            <Database className="w-3 h-3 text-zinc-500" />
                            <span className="text-[10px] text-zinc-400">Corpus Size</span>
                        </div>
                        <span className="text-sm font-bold text-emerald-400/90">65M Tokens</span>
                    </div>
                </div>
            </div>

        </div>
    );
}
