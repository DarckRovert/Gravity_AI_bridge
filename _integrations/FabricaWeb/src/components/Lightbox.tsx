"use client";

import { useState, useEffect } from 'react';
import Image from 'next/image';

interface LightboxProps {
    images: string[];
    index: number | null;
    onClose: () => void;
}

export default function Lightbox({ images, index, onClose }: LightboxProps) {
    const [currentIndex, setCurrentIndex] = useState<number | null>(index);

    useEffect(() => {
        setCurrentIndex(index);
    }, [index]);

    useEffect(() => {
        const handleEsc = (e: KeyboardEvent) => {
            if (e.key === 'Escape') onClose();
            if (e.key === 'ArrowRight') handleNext();
            if (e.key === 'ArrowLeft') handlePrev();
        };
        window.addEventListener('keydown', handleEsc);
        return () => window.removeEventListener('keydown', handleEsc);
    }, [currentIndex]);

    if (currentIndex === null) return null;

    const handleNext = () => setCurrentIndex(prev => (prev! + 1) % images.length);
    const handlePrev = () => setCurrentIndex(prev => (prev! - 1 + images.length) % images.length);

    return (
        <div
            className="fixed inset-0 z-[200] bg-black/90 backdrop-blur-md flex items-center justify-center p-4 md:p-12 animate-in fade-in duration-500"
            onClick={onClose}
        >
            {/* Glossy Close Command */}
            <button
                className="absolute top-8 right-8 text-white/70 hover:text-white bg-white/10 hover:bg-white/20 w-12 h-12 rounded-full flex items-center justify-center backdrop-blur-xl border border-white/20 transition-all hover:rotate-90 z-[210] shadow-2xl"
                onClick={onClose}
                aria-label="Cerrar"
            >
                <span className="text-2xl font-light">✕</span>
            </button>

            {/* Navigation Arrows - Glassmorphism */}
            <button
                className="absolute left-8 lg:left-12 text-white/50 hover:text-white bg-white/5 hover:bg-white/10 w-16 h-16 rounded-full flex items-center justify-center backdrop-blur-md border border-white/10 transition-all active:scale-90 z-[210] hidden md:flex"
                onClick={(e) => { e.stopPropagation(); handlePrev(); }}
            >
                <span className="text-4xl">‹</span>
            </button>

            <button
                className="absolute right-8 lg:right-12 text-white/50 hover:text-white bg-white/5 hover:bg-white/10 w-16 h-16 rounded-full flex items-center justify-center backdrop-blur-md border border-white/10 transition-all active:scale-90 z-[210] hidden md:flex"
                onClick={(e) => { e.stopPropagation(); handleNext(); }}
            >
                <span className="text-4xl">›</span>
            </button>

            {/* Main Image Container */}
            <div
                className="relative w-full max-w-6xl h-full flex flex-col items-center justify-center"
                onClick={(e) => e.stopPropagation()}
            >
                <div className="relative w-full h-full max-h-[80vh] group">
                    <Image
                        src={images[currentIndex]}
                        alt={`Gallery Item ${currentIndex + 1}`}
                        fill
                        className="object-contain drop-shadow-[0_35px_35px_rgba(0,0,0,0.5)] transition-all duration-700"
                        priority
                    />

                    {/* Caption Overlay */}
                    <div className="absolute -bottom-16 left-1/2 -translate-x-1/2 w-full text-center px-4">
                        <p className="text-paper font-playfair italic text-lg opacity-90 tracking-wide">
                            "Postre artesanal – Hecho con amor"
                        </p>
                        <div className="mt-4 flex justify-center gap-2">
                            {images.map((_, i) => (
                                <div
                                    key={i}
                                    className={`h-1 rounded-full transition-all duration-500 ${i === currentIndex ? 'w-8 bg-white' : 'w-2 bg-white/20'}`}
                                />
                            ))}
                        </div>
                    </div>
                </div>
            </div>

            {/* Tooltip Mobile */}
            <div className="absolute top-8 left-1/2 -translate-x-1/2 bg-white/10 backdrop-blur-xl border border-white/10 px-4 py-1 rounded-full text-white/50 text-[10px] md:hidden tracking-widest uppercase">
                Slide para navegar
            </div>
        </div>
    );
}
