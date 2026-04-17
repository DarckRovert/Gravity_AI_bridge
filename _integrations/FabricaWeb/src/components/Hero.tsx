"use client";

import { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { useContent } from '@/context/SiteConfigContext';

const HERO_IMAGES = [
    '/img/products/pionono-choco-frutos.jpg',
    '/img/products/cake-chocolate.jpg',
    '/img/products/cake-marmoleado.jpg',
];

const SLIDE_INTERVAL = 5000;

export default function Hero() {
    const { content } = useContent();
    const [current, setCurrent] = useState(0);
    const [transitioning, setTransitioning] = useState(false);

    const advance = useCallback(() => {
        setTransitioning(true);
        setTimeout(() => {
            setCurrent(i => (i + 1) % HERO_IMAGES.length);
            setTransitioning(false);
        }, 400);
    }, []);

    useEffect(() => {
        const id = setInterval(advance, SLIDE_INTERVAL);
        return () => clearInterval(id);
    }, [advance]);

    const goTo = (idx: number) => {
        if (idx === current) return;
        setTransitioning(true);
        setTimeout(() => {
            setCurrent(idx);
            setTransitioning(false);
        }, 400);
    };

    const titleParts = content.heroTitle.split('\n');

    return (
        <section className="relative min-h-[90vh] flex items-center justify-center overflow-hidden pt-20">
            {/* Carousel backgrounds */}
            {HERO_IMAGES.map((src, idx) => (
                <div
                    key={src}
                    className={`absolute inset-0 z-0 transition-opacity duration-700 ${idx === current && !transitioning ? 'opacity-100' : 'opacity-0'}`}
                >
                    <Image
                        src={src}
                        alt={`Slide ${idx + 1}`}
                        fill
                        priority={idx === 0}
                        placeholder="blur"
                        blurDataURL="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mO8+v//fwAJagPlD4GMyAAAAABJRU5ErkJggg=="
                        className="object-cover object-center"
                        quality={idx === 0 ? 90 : 75}
                        sizes="100vw"
                    />
                </div>
            ))}

            {/* Dark/Tropical Overlay */}
            <div className="absolute inset-0 z-10 bg-gradient-to-b from-primary/80 via-primary/60 to-primary/95" />

            <div className="container mx-auto px-4 relative z-20 text-center">
                <div className="max-w-4xl mx-auto">
                    <h1 className="text-5xl md:text-8xl font-fredoka font-bold text-paper leading-tight mb-8 drop-shadow-2xl animate-fade-up">
                        {titleParts.length > 1 ? (
                            <>
                                {titleParts[0]} <br />
                                <span className="text-secondary italic">{titleParts[1]}</span>
                            </>
                        ) : (
                            content.heroTitle
                        )}
                    </h1>

                    <p className="text-xl md:text-2xl text-paper mb-12 leading-relaxed opacity-90 max-w-2xl mx-auto font-nunito animate-fade-up" style={{ animationDelay: '0.2s' }}>
                        {content.heroSubtitle}
                    </p>

                    <div className="flex flex-wrap justify-center gap-4 sm:gap-6 mb-16 animate-fade-up" style={{ animationDelay: '0.4s' }}>
                        <Link
                            href="/menu"
                            className="bg-accent text-white px-8 sm:px-10 py-4 rounded-full font-bold text-base sm:text-lg hover:bg-secondary hover:text-primary hover:-translate-y-1 transition-all shadow-xl uppercase tracking-widest"
                        >
                            {content.heroCtaText}
                        </Link>
                        <a
                            href={`https://wa.me/${content.whatsappNumber}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="bg-white/10 backdrop-blur-sm border-2 border-paper text-paper px-8 sm:px-10 py-4 rounded-full font-bold text-base sm:text-lg hover:bg-paper hover:text-primary transition-all uppercase tracking-widest"
                        >
                            Pedir por WhatsApp
                        </a>
                    </div>

                    <div className="inline-flex flex-wrap justify-center gap-8 md:gap-16 p-6 md:p-8 bg-black/20 backdrop-blur-md rounded-[2rem] border border-white/10 shadow-2xl animate-fade-up" style={{ animationDelay: '0.6s' }}>
                        {[
                            { icon: '⚡', label: 'Entrega Rápida' },
                            { icon: '🍓', label: 'Fruta Fresca' },
                            { icon: '🥟', label: 'Hecho en Casa' },
                        ].map(({ icon, label }) => (
                            <div key={label} className="flex items-center gap-3">
                                <span className="text-3xl filter drop-shadow-md">{icon}</span>
                                <span className="font-semibold text-paper text-sm md:text-base">{label}</span>
                            </div>
                        ))}
                    </div>
                </div>
            </div>

            {/* Carousel dots */}
            <div className="absolute bottom-20 left-1/2 -translate-x-1/2 z-20 flex gap-2">
                {HERO_IMAGES.map((_, idx) => (
                    <button
                        key={idx}
                        onClick={() => goTo(idx)}
                        aria-label={`Imagen ${idx + 1}`}
                        className={`rounded-full transition-all duration-300 ${idx === current ? 'bg-secondary w-6 h-2' : 'bg-white/40 w-2 h-2 hover:bg-white/70'}`}
                    />
                ))}
            </div>

            {/* Scroll Indicator */}
            <div className="absolute bottom-8 left-1/2 -translate-x-1/2 z-20 animate-bounce cursor-pointer opacity-50 hover:opacity-100 transition-opacity">
                <a href="#menu" className="text-paper text-2xl">↓</a>
            </div>
        </section>
    );
}
