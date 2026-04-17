"use client";

import { useState, useEffect } from 'react';

export default function ScrollToTop() {
    const [isVisible, setIsVisible] = useState(false);

    useEffect(() => {
        const toggleVisibility = () => {
            if (window.pageYOffset > 500) {
                setIsVisible(true);
            } else {
                setIsVisible(false);
            }
        };

        window.addEventListener('scroll', toggleVisibility);
        return () => window.removeEventListener('scroll', toggleVisibility);
    }, []);

    const scrollToTop = () => {
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    };

    if (!isVisible) return null;

    return (
        <button
            onClick={scrollToTop}
            className="fixed bottom-24 right-6 z-40 bg-primary/80 backdrop-blur-sm text-white w-12 h-12 rounded-full shadow-lg border border-white/10 flex items-center justify-center hover:bg-primary hover:scale-110 transition-all duration-300 animate-reveal cursor-pointer"
            aria-label="Volver arriba"
        >
            <span className="text-xl">↑</span>
        </button>
    );
}
