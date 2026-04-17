"use client";

import { useState, useEffect, useCallback, useRef } from 'react';
import { useTestimonials } from '@/context/SiteConfigContext';

export default function TestimonialCarousel() {
    const { testimonials } = useTestimonials();
    const [current, setCurrent] = useState(0);
    const touchStartX = useRef<number | null>(null);

    const prev = useCallback(() => {
        setCurrent(i => (i - 1 + (testimonials.length || 1)) % (testimonials.length || 1));
    }, [testimonials.length]);

    const next = useCallback(() => {
        setCurrent(prev => (prev + 1) % (testimonials.length || 1));
    }, [testimonials.length]);

    useEffect(() => {
        if (testimonials.length === 0) return;
        const timer = setInterval(next, 5000);
        return () => clearInterval(timer);
    }, [next, testimonials.length]);

    // Touch / swipe support
    const onTouchStart = (e: React.TouchEvent) => {
        touchStartX.current = e.touches[0].clientX;
    };
    const onTouchEnd = (e: React.TouchEvent) => {
        if (touchStartX.current === null) return;
        const diff = touchStartX.current - e.changedTouches[0].clientX;
        if (Math.abs(diff) > 40) diff > 0 ? next() : prev();
        touchStartX.current = null;
    };

    if (testimonials.length === 0) return null;

    return (
        <section className="py-20 bg-paper">
            <div className="container mx-auto px-4 text-center">
                <h2 className="text-4xl font-playfair font-bold text-primary mb-2">Clientes Felices</h2>
                <p className="text-secondary font-medium mb-12 uppercase tracking-widest text-xs">Sus palabras son nuestra mejor receta</p>

                <div className="relative max-w-2xl mx-auto">
                    {/* Arrow controls */}
                    {testimonials.length > 1 && (
                        <>
                            <button onClick={prev} aria-label="Anterior" className="absolute left-0 top-1/2 -translate-y-1/2 -translate-x-4 z-10 w-9 h-9 bg-white rounded-full shadow-md border border-gray-100 hover:bg-secondary hover:text-white transition-all hidden sm:flex items-center justify-center text-primary font-bold">‹</button>
                            <button onClick={next} aria-label="Siguiente" className="absolute right-0 top-1/2 -translate-y-1/2 translate-x-4 z-10 w-9 h-9 bg-white rounded-full shadow-md border border-gray-100 hover:bg-secondary hover:text-white transition-all hidden sm:flex items-center justify-center text-primary font-bold">›</button>
                        </>
                    )}

                    {/* Cards — swipeable */}
                    <div
                        className="overflow-hidden"
                        onTouchStart={onTouchStart}
                        onTouchEnd={onTouchEnd}
                    >
                        {testimonials.map((t, i) => (
                            <div
                                key={i}
                                className={`transition-all duration-700 ease-in-out ${i === current
                                    ? 'opacity-100 translate-x-0'
                                    : 'opacity-0 absolute inset-0 translate-x-8 pointer-events-none'
                                    }`}
                            >
                                <div className="bg-white p-8 sm:p-10 rounded-3xl shadow-lg border border-primary/5">
                                    <div className="text-accent mb-4 text-xl">⭐⭐⭐⭐⭐</div>
                                    <p className="italic text-gray-600 mb-6 text-base sm:text-lg leading-relaxed">&ldquo;{t.text}&rdquo;</p>
                                    <h4 className="font-bold text-primary text-base sm:text-lg">— {t.name}</h4>
                                </div>
                            </div>
                        ))}
                    </div>

                    {/* Dots */}
                    <div className="flex justify-center gap-3 mt-8">
                        {testimonials.map((_, i) => (
                            <button
                                key={i}
                                onClick={() => setCurrent(i)}
                                className={`rounded-full transition-all duration-300 ${i === current
                                    ? 'bg-secondary w-6 h-3 scale-100'
                                    : 'w-3 h-3 bg-primary/20 hover:bg-primary/40'
                                    }`}
                                aria-label={`Testimonio ${i + 1}`}
                            />
                        ))}
                    </div>
                </div>
            </div>
        </section>
    );
}
