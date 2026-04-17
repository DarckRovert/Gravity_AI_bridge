"use client";

import { useState, useRef, MouseEvent } from 'react';

interface NFTCardProps {
    id: string;
    label: string;
    rarity?: string;
    imageUrl?: string;
    network?: string; // 'Amoy Testnet' or 'Polygon Mainnet'
}

export default function NFTCard({ id, label, rarity = "Legendary", imageUrl, network = "Polygon Amoy" }: NFTCardProps) {
    const cardRef = useRef<HTMLDivElement>(null);
    const [rotate, setRotate] = useState({ x: 0, y: 0 });
    const [subtle, setSubtle] = useState(false);

    const handleMouseMove = (e: MouseEvent<HTMLDivElement>) => {
        if (!cardRef.current) return;

        const rect = cardRef.current.getBoundingClientRect();
        const width = rect.width;
        const height = rect.height;

        const mouseX = e.clientX - rect.left;
        const mouseY = e.clientY - rect.top;

        const rotateY = ((mouseX - width / 2) / width) * 20; // Max 20deg
        const rotateX = ((height / 2 - mouseY) / height) * 20;

        setRotate({ x: rotateX, y: rotateY });
    };

    const handleMouseLeave = () => {
        setRotate({ x: 0, y: 0 });
        setSubtle(true);
        setTimeout(() => setSubtle(false), 500); // Reset animation
    };

    return (
        <div
            className="perspective-1000 w-64 h-80 mx-auto my-4 cursor-pointer"
            onMouseMove={handleMouseMove}
            onMouseLeave={handleMouseLeave}
        >
            <div
                ref={cardRef}
                className={`
                    relative w-full h-full rounded-2xl transition-transform duration-100 ease-out shadow-2xl
                    ${subtle ? 'duration-500' : ''}
                `}
                style={{
                    transform: `rotateX(${rotate.x}deg) rotateY(${rotate.y}deg)`,
                    transformStyle: 'preserve-3d',
                }}
            >
                {/* 🌈 Holo Gradient Background */}
                <div className="absolute inset-0 rounded-2xl bg-gradient-to-br from-indigo-900 via-purple-900 to-pink-900 overflow-hidden border border-white/20 group-hover:border-white/40 transition-colors">

                    {/* What is this? Tooltip Icon */}
                    <div className="absolute top-2 right-2 z-20 group/tooltip">
                        <div className="w-6 h-6 rounded-full bg-white/10 backdrop-blur-md flex items-center justify-center text-white/70 text-xs font-bold border border-white/20 cursor-help hover:bg-white/30 transition-colors">
                            ?
                        </div>
                        <div className="absolute right-0 top-8 w-48 p-3 rounded-xl bg-black/80 backdrop-blur-xl border border-white/20 text-white text-[10px] opacity-0 group-hover/tooltip:opacity-100 transition-opacity pointer-events-none z-30 shadow-2xl">
                            <span className="font-bold text-purple-300 block mb-1">¿Qué es un NFT?</span>
                            Es un certificado digital de autenticidad y propiedad de tu torta, guardado de por vida en la blockchain de Polygon.
                        </div>
                    </div>

                    {/* Noise Texture */}
                    {/* Noise Texture (Inlined for safety) */}
                    <div className="absolute inset-0 opacity-20" style={{ backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.65' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)' opacity='1'/%3E%3C/svg%3E")` }} />

                    {/* Image Placeholder or Actual Image */}
                    <div className="absolute top-4 left-4 right-4 h-40 bg-white/10 rounded-xl backdrop-blur-sm flex items-center justify-center overflow-hidden border border-white/10 shadow-inner group">
                        {imageUrl ? (
                            // eslint-disable-next-line @next/next/no-img-element
                            <img src={imageUrl} alt={label} className="w-full h-full object-cover" />
                        ) : (
                            <span className="text-4xl filter drop-shadow-[0_0_10px_rgba(255,255,255,0.5)]">🎂</span>
                        )}
                        {/* Shine effect on image */}
                        <div className="absolute inset-0 bg-gradient-to-tr from-transparent via-white/20 to-transparent translate-x-[-150%] group-hover:translate-x-[150%] transition-transform duration-1000" />
                    </div>

                    {/* Metadata */}
                    <div className="absolute bottom-4 left-4 right-4 text-white">
                        <div className="flex justify-between items-end mb-2">
                            <div>
                                <p className="text-[10px] text-purple-200 uppercase tracking-widest font-bold">Proof of Cake</p>
                                <h3 className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-yellow-200 to-amber-400 font-playfair">{label}</h3>
                            </div>
                            <div className="text-right">
                                <span className={`
                                    text-[10px] font-bold px-2 py-0.5 rounded-full border 
                                    ${rarity === 'Legendary' ? 'bg-amber-500/20 border-amber-400 text-amber-300' : 'bg-blue-500/20 border-blue-400 text-blue-300'}
                                `}>
                                    {rarity}
                                </span>
                            </div>
                        </div>

                        <div className="flex justify-between items-center text-[10px] opacity-70 font-mono border-t border-white/10 pt-2">
                            <span>ID: #{id.slice(-6)}</span>
                            <span className="flex items-center gap-1">
                                <span className={`w-1.5 h-1.5 rounded-full ${network.includes('Amoy') ? 'bg-yellow-400' : 'bg-purple-500'} animate-pulse`}></span>
                                {network}
                            </span>
                        </div>
                    </div>

                    {/* ✨ Holographic Overlay (The magic sauce) */}
                    <div
                        className="absolute inset-0 rounded-2xl pointer-events-none"
                        style={{
                            background: `linear-gradient(115deg, transparent 0%, rgba(255,255,255,0.3) ${40 + rotate.y}%, transparent 60%)`,
                            opacity: 0.8,
                            mixBlendMode: 'overlay',
                        }}
                    />
                    <div
                        className="absolute inset-0 rounded-2xl pointer-events-none"
                        style={{
                            background: `linear-gradient(115deg, transparent 30%, rgba(255,0,255,0.3) ${50 - rotate.x}%, transparent 80%)`,
                            opacity: 0.5,
                            mixBlendMode: 'color-dodge',
                        }}
                    />
                </div>
            </div>
        </div >
    );
}
