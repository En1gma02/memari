"use client";

import { motion } from "framer-motion";
import { HeroSection } from "@/components/landing/hero-section";
import { PipelineArchitecture } from "@/components/landing/pipeline-architecture";
import { BenchmarkStats } from "@/components/landing/benchmark-stats";
import { MemoryLayers } from "@/components/landing/memory-layers";
import { ToolRegistry } from "@/components/landing/tool-registry";
import { SocialLinks } from "@/components/landing/social-links";

// Staggered container animation
const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
        opacity: 1,
        transition: {
            staggerChildren: 0.1,
            delayChildren: 0.2,
        },
    },
};

// Precise, technical entrance
const cardVariants = {
    hidden: { opacity: 0, scale: 0.95, y: 10 },
    visible: {
        opacity: 1,
        scale: 1,
        y: 0,
        transition: {
            duration: 0.4,
            ease: [0.23, 1, 0.32, 1] as const,
        },
    },
};

// Glass Card Shell
const glassPanel = "bg-[#050505]/80 backdrop-blur-xl border border-white/10 rounded-3xl overflow-hidden relative shadow-2xl";

export default function LandingPage() {
    return (
        <div className="h-screen w-screen overflow-hidden bg-black text-white relative font-sans selection:bg-emerald-500/30 selection:text-emerald-200">

            {/* Global Atmosphere */}
            <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,_var(--tw-gradient-stops))] from-neutral-900/40 via-black to-black pointer-events-none" />

            {/* Engineering Grid Overlay */}
            <div
                className="absolute inset-0 opacity-[0.05] pointer-events-none z-0 mix-blend-screen"
                style={{
                    backgroundImage: 'linear-gradient(rgba(255, 255, 255, 0.1) 1px, transparent 1px), linear-gradient(90deg, rgba(255, 255, 255, 0.1) 1px, transparent 1px)',
                    backgroundSize: '100px 100px'
                }}
            />

            <motion.main
                className="relative z-20 h-full w-full p-4 md:p-6 lg:p-8 flex items-center justify-center"
                variants={containerVariants}
                initial="hidden"
                animate="visible"
            >
                {/* 12-COLUMN ASYMMETRIC GRID */}
                <div className="w-full max-w-[1700px] h-full max-h-[920px] grid grid-cols-1 lg:grid-cols-12 gap-6 p-2">

                    {/* LEFT COLUMN: Sidebar (Span 3 - 25%) */}
                    <div className="col-span-1 lg:col-span-3 flex flex-col gap-4 h-full min-h-0">

                        {/* 1. Hero Section */}
                        <motion.div variants={cardVariants} className="flex-none relative group">
                            <div className="absolute inset-0 bg-emerald-500/5 blur-[100px] -z-10 rounded-full opacity-0 group-hover:opacity-100 transition-opacity duration-700" />
                            <div className={`${glassPanel} p-6 hover:border-white/20 transition-colors h-full`}>
                                <HeroSection />
                            </div>
                        </motion.div>

                        {/* 2. Benchmark Stats (Moved here) */}
                        <motion.div variants={cardVariants} className="flex-1 min-h-0">
                            <BenchmarkStats />
                        </motion.div>

                        {/* 3. Social Links */}
                        <motion.div variants={cardVariants} className="flex-none">
                            <SocialLinks />
                        </motion.div>

                    </div>

                    {/* RIGHT COLUMN: Dashboard (Span 9 - 75%) */}
                    <div className="col-span-1 lg:col-span-9 flex flex-col gap-4 h-full min-h-0">

                        {/* Top: Pipeline Architecture (Full Width) */}
                        <motion.div variants={cardVariants} className="flex-[1.4] min-h-0">
                            <PipelineArchitecture />
                        </motion.div>

                        {/* Bottom: Nested Grid */}
                        <div className="flex-1 min-h-0 grid grid-cols-1 md:grid-cols-2 gap-4">

                            {/* Memory Layers (Left Slot) */}
                            <motion.div variants={cardVariants} className="h-full min-h-0">
                                <MemoryLayers />
                            </motion.div>

                            {/* Tool Registry (Right Slot - Moved here) */}
                            <motion.div variants={cardVariants} className="h-full min-h-0">
                                <ToolRegistry />
                            </motion.div>

                        </div>

                    </div>

                </div>
            </motion.main>

        </div>
    );
}
