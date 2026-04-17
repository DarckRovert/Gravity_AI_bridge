"use client";

import { useState, useEffect, useRef } from 'react';
import { usePromotions } from '@/context/SiteConfigContext';

export default function PromoBanner() {
    const { promotions } = usePromotions();
    const [isVisible, setIsVisible] = useState(false);
    const [promo, setPromo] = useState({ text: '', link: '' });
    const hasInitialized = useRef(false);

    useEffect(() => {
        if (promotions.length === 0 || hasInitialized.current) return;
        hasInitialized.current = true;

        const randomPromo = promotions[Math.floor(Math.random() * promotions.length)];
        setPromo(randomPromo);

        const timer = setTimeout(() => setIsVisible(true), 1500);
        return () => clearTimeout(timer);
    }, [promotions]);

    if (!isVisible || !promo.text) return null;

    return (
        <div className="bg-primary text-paper py-2 px-4 text-center text-sm font-medium animate-reveal relative z-50">
            <a href={promo.link} className="hover:underline">
                {promo.text}
            </a>
            <button
                onClick={() => setIsVisible(false)}
                className="absolute right-4 top-1/2 -translate-y-1/2 opacity-60 hover:opacity-100"
            >
                ✕
            </button>
        </div>
    );
}
