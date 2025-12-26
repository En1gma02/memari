"use client";

import Image from "next/image";
import Link from "next/link";

export function SocialLinks() {
    const socials = [
        {
            name: "HuggingFace",
            icon: "/huggingface-color.png",
            href: "https://huggingface.co/En1gma02",
            size: 24
        },
        {
            name: "GitHub",
            icon: "/github.png",
            href: "https://github.com/En1gma02",
            size: 22 // Adjusting for visual balance
        },
        {
            name: "Gmail",
            icon: "/gmail.png",
            href: "mailto:akshansh2624@gmail.com",
            size: 20
        }
    ];

    return (
        <div className="w-full bg-[#050505] border border-white/10 rounded-2xl p-4 flex justify-around items-center">
            {socials.map((social) => (
                <Link
                    key={social.name}
                    href={social.href}
                    target={social.href.startsWith("mailto") ? undefined : "_blank"}
                    className="p-3 rounded-xl bg-white/5 border border-white/5 hover:bg-white/10 hover:scale-110 hover:border-white/20 transition-all duration-300 group relative"
                >
                    <div className="relative w-6 h-6 flex items-center justify-center">
                        <Image
                            src={social.icon}
                            alt={social.name}
                            width={social.size}
                            height={social.size}
                            className="object-contain opacity-80 group-hover:opacity-100 transition-opacity"
                        />
                    </div>
                </Link>
            ))}
        </div>
    );
}
