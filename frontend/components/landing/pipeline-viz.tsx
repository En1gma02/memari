"use client";

import { motion } from "framer-motion";
import { useState } from "react";
import {
    MessageSquare,
    Scissors,
    BrainCircuit,
    Database,
    GitMerge,
} from "lucide-react";

interface NodeData {
    id: string;
    label: string;
    sublabel: string;
    xPct: number; // Percentage 0-100
    yPct: number; // Percentage 0-100
    icon: React.ElementType;
    details: { label: string; value: string }[];
}

const nodes: NodeData[] = [
    {
        id: "input",
        label: "Message",
        sublabel: "User Input",
        xPct: 15,
        yPct: 50,
        icon: MessageSquare,
        details: [
            { label: "Type", value: "Raw Text" },
            { label: "Lang", value: "En/Hi Mixed" }
        ],
    },
    {
        id: "chunking",
        label: "Session",
        sublabel: "Chunking",
        xPct: 32.5,
        yPct: 50,
        icon: Scissors,
        details: [
            { label: "Split", value: "Dynamic" },
            { label: "Total", value: "93 Sessions" }
        ],
    },
    {
        id: "rewriting",
        label: "LLM",
        sublabel: "Rewriting",
        xPct: 50,
        yPct: 50,
        icon: BrainCircuit,
        details: [
            { label: "Model", value: "Cerebras 8B" },
            { label: "Latency", value: "120ms" }
        ],
    },
    {
        id: "vectordb",
        label: "Vector DB",
        sublabel: "FAISS Index",
        xPct: 67.5,
        yPct: 50,
        icon: Database,
        details: [
            { label: "Dim", value: "384" },
            { label: "Metric", value: "Cosine" }
        ],
    },
    {
        id: "fusion",
        label: "Fusion",
        sublabel: "Retrieval",
        xPct: 85,
        yPct: 50,
        icon: GitMerge,
        details: [
            { label: "Hybrid", value: "BM25 + Vec" },
            { label: "Rerank", value: "CrossEncoder" }
        ],
    },
];

const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
        opacity: 1,
        transition: {
            staggerChildren: 0.2,
            delayChildren: 0.1,
        },
    },
};

export function PipelineViz() {
    const [hoveredNode, setHoveredNode] = useState<string | null>(null);

    return (
        <div className="w-full h-full flex items-center justify-center relative min-h-[200px]">
            {/* Background Grid Pattern for Technical Feel */}
            <div
                className="absolute inset-0 z-0 opacity-[0.07]"
                style={{
                    backgroundImage: 'linear-gradient(rgba(255, 255, 255, 0.1) 1px, transparent 1px), linear-gradient(90deg, rgba(255, 255, 255, 0.1) 1px, transparent 1px)',
                    backgroundSize: '40px 40px',
                    backgroundPosition: 'center'
                }}
            />

            <motion.div
                initial="hidden"
                animate="visible"
                variants={containerVariants}
                className="relative z-10 w-full h-full max-w-[1000px] flex items-center justify-center"
            >
                <div className="relative w-full aspect-4/1 max-h-[250px]">
                    <svg className="absolute inset-0 w-full h-full overflow-visible pointer-events-none">
                        <defs>
                            <filter id="glow-line" x="-20%" y="-20%" width="140%" height="140%">
                                <feGaussianBlur stdDeviation="2" result="blur" />
                                <feComposite in="SourceGraphic" in2="blur" operator="over" />
                            </filter>
                        </defs>

                        {/* Connection Lines */}
                        {nodes.slice(0, -1).map((node, i) => {
                            const nextNode = nodes[i + 1];
                            return (
                                <g key={`connection-${i}`}>
                                    {/* Base dim line */}
                                    <line
                                        x1={`${node.xPct + 4}%`} // +4 offset for node radius approx
                                        y1={`${node.yPct}%`}
                                        x2={`${nextNode.xPct - 4}%`}
                                        y2={`${nextNode.yPct}%`}
                                        stroke="rgba(255,255,255,0.05)"
                                        strokeWidth="1"
                                    />

                                    {/* Flowing data packet */}
                                    <motion.circle
                                        r="2"
                                        fill="#10b981"
                                        filter="url(#glow-line)"
                                        initial={{ cx: `${node.xPct + 4}%`, cy: `${node.yPct}%` }}
                                        animate={{
                                            cx: [`${node.xPct + 4}%`, `${nextNode.xPct - 4}%`],
                                            opacity: [0, 1, 0]
                                        }}
                                        transition={{
                                            duration: 1.5,
                                            ease: "linear",
                                            repeat: Infinity,
                                            delay: i * 0.4
                                        }}
                                    />
                                </g>
                            );
                        })}
                    </svg>

                    {/* Nodes */}
                    {nodes.map((node) => {
                        const isHovered = hoveredNode === node.id;

                        return (
                            <motion.div
                                key={node.id}
                                className="absolute"
                                style={{ left: `${node.xPct}%`, top: `${node.yPct}%` }}
                                initial={{ scale: 0, opacity: 0 }}
                                variants={{
                                    visible: {
                                        scale: 1,
                                        opacity: 1,
                                        transition: { type: "spring" as const, stiffness: 260, damping: 20 }
                                    }
                                }}
                            >
                                <motion.div
                                    className={`
                            relative -translate-x-1/2 -translate-y-1/2 w-[60px] h-[60px] md:w-[70px] md:h-[70px] 
                            flex flex-col items-center justify-center 
                            rounded-xl border backdrop-blur-md cursor-pointer transition-all duration-300
                            ${isHovered
                                            ? "bg-emerald-500/10 border-emerald-500/50 shadow-[0_0_30px_-5px_rgba(16,185,129,0.3)] z-50 scale-110"
                                            : "bg-white/5 border-white/10 hover:border-emerald-500/30"
                                        }
                        `}
                                    onMouseEnter={() => setHoveredNode(node.id)}
                                    onMouseLeave={() => setHoveredNode(null)}
                                >
                                    <node.icon
                                        className={`w-5 h-5 md:w-6 md:h-6 mb-1 md:mb-2 transition-colors duration-300 ${isHovered ? "text-emerald-400" : "text-emerald-500/70"}`}
                                        strokeWidth={1.5}
                                    />
                                    <span className="text-[8px] md:text-[10px] font-medium text-white/90 font-sans tracking-tight">{node.label}</span>

                                    {/* Tooltip Card */}
                                    <div
                                        className={`
                                absolute top-full mt-4 w-[140px] p-3 rounded-lg 
                                bg-[#0a0a0a]/90 border border-emerald-500/20 backdrop-blur-xl
                                shadow-2xl transition-all duration-300 pointer-events-none z-50
                                ${isHovered ? "opacity-100 translate-y-0" : "opacity-0 -translate-y-2"}
                            `}
                                    >
                                        <div className="absolute -top-1 left-1/2 -translate-x-1/2 w-2 h-2 bg-[#0a0a0a]/90 border-t border-l border-emerald-500/20 rotate-45" />
                                        <div className="space-y-2">
                                            <p className="text-[10px] uppercase tracking-widest text-emerald-500/60 font-mono border-b border-white/5 pb-1 mb-1 text-left">
                                                {node.sublabel}
                                            </p>
                                            {node.details.map((d, i) => (
                                                <div key={i} className="flex justify-between items-center text-[10px]">
                                                    <span className="text-white/40">{d.label}</span>
                                                    <span className="text-white/90 font-mono">{d.value}</span>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                </motion.div>
                            </motion.div>
                        );
                    })}
                </div>
            </motion.div>
        </div>
    );
}
