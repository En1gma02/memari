import Link from "next/link";

export function HeroSection() {
    return (
        <div className="h-full flex flex-col justify-between p-4">
            <div className="space-y-4">
                {/* Version Badge */}
                <div className="flex items-center gap-2">
                    <div className="w-2 h-2 bg-emerald-500 animate-pulse rounded-full" />
                    <span className="font-mono text-[10px] text-emerald-500/80 tracking-widest uppercase">
                        v2.1.0-beta
                    </span>
                </div>

                {/* Title */}
                <h1 className="text-4xl md:text-5xl font-bold tracking-tighter text-white uppercase">
                    MEMARI
                </h1>

                {/* Subtitle with Technical Context */}
                <div className="space-y-1">
                    <p className="text-xs font-mono text-white/50 leading-relaxed">
                        Tool Calling based Fusion ReRanker RAG architecture for Long-Term Persistent memory with user and agent personas.
                    </p>
                </div>
            </div>

            {/* Terminal Style CTA - Solid Attention Grabber */}
            <Link href="/chat" className="group w-fit">
                <div className="bg-emerald-500 rounded-lg px-4 py-2.5 flex items-center justify-start gap-2 transition-all duration-300 hover:bg-emerald-400 hover:shadow-[0_0_20px_rgba(16,185,129,0.4)] hover:scale-[1.02]">
                    <div className="font-mono text-xs font-bold text-black tracking-tight flex items-center gap-2">
                        <span>&gt;_ .start-demo.sh</span>
                        <span className="w-1.5 h-3.5 bg-black/80 animate-pulse" />
                    </div>
                </div>
            </Link>
        </div>
    );
}
