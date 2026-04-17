"use client";

import { useState, useEffect } from 'react';
import { useToast } from '@/context/ToastContext';
import { useLayout } from '@/context/SiteConfigContext';
import dynamic from 'next/dynamic';

const WorldIDVerify = dynamic(() => import('./WorldIDVerify'), { ssr: false });

export default function NewsletterModal() {
    const [isVisible, setIsVisible] = useState(false);
    const [email, setEmail] = useState('');
    const { showToast } = useToast();
    const { layout } = useLayout();

    useEffect(() => {
        if (!layout.showNewsletter) return;
        const hasShown = localStorage.getItem('pastelito_newsletter_shown');
        if (!hasShown) {
            const timer = setTimeout(() => {
                setIsVisible(true);
            }, 8000); // 8s delay for better UX
            return () => clearTimeout(timer);
        }
    }, [layout.showNewsletter]);

    const handleClose = () => {
        setIsVisible(false);
        localStorage.setItem('pastelito_newsletter_shown', 'true');
    };

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();

        // Basic validation & sanitization
        const sanitizedEmail = email.trim().toLowerCase();
        if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(sanitizedEmail)) {
            showToast("⚠️ Por favor ingresa un correo válido.", "error");
            return;
        }

        showToast("¡Gracias por suscribirte! 🧁 Pronto recibirás nuestras mejores ofertas.", "success");
        handleClose();
    };

    if (!isVisible) return null;

    return (
        <div
            className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/40 backdrop-blur-md animate-in fade-in duration-500"
            role="dialog"
            aria-modal="true"
            aria-labelledby="newsletter-heading"
        >
            <div className="bg-paper rounded-[2.5rem] overflow-hidden max-w-lg w-full shadow-[0_30px_100px_rgba(0,0,0,0.3)] relative border border-primary/10">

                {/* Visual Accent */}
                <div className="h-32 bg-gradient-to-r from-primary via-primary/70 to-primary flex items-center justify-center relative">
                    <div className="absolute inset-0 bg-[url('/img/pattern.png')] opacity-10 mix-blend-overlay" />
                    <span className="text-6xl drop-shadow-lg">✨</span>
                </div>

                <button
                    onClick={handleClose}
                    className="absolute top-6 right-6 text-white/70 hover:text-white bg-black/10 hover:bg-black/20 w-10 h-10 rounded-full flex items-center justify-center transition-all z-10"
                    aria-label="Cerrar"
                >✕</button>

                <div className="p-10 text-center space-y-6">
                    <div className="space-y-2">
                        <h2 id="newsletter-heading" className="text-3xl font-playfair font-bold text-primary leading-tight">
                            ¿Un regalito dulce? 🧁
                        </h2>
                        <p className="text-gray-500 font-medium">
                            Únete a nuestro club de amantes del postre y obtén un <span className="text-secondary font-bold">10% OFF</span> en tu primer pedido.
                        </p>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
                        <form onSubmit={handleSubmit} className="space-y-4">
                            <div className="relative group">
                                <input
                                    type="email"
                                    required
                                    aria-required="true"
                                    placeholder="tu@correo.com"
                                    className="w-full h-14 pl-6 pr-12 bg-white border border-primary/20 rounded-2xl outline-none focus:ring-2 focus:ring-secondary/30 focus:border-secondary transition-all text-gray-700 shadow-inner group-hover:border-secondary/50"
                                    value={email}
                                    onChange={e => setEmail(e.target.value)}
                                />
                                <span className="absolute right-5 top-1/2 -translate-y-1/2 opacity-30">💌</span>
                            </div>

                            <button
                                type="submit"
                                className="w-full h-14 bg-primary text-white rounded-2xl font-bold text-sm hover:bg-secondary hover:shadow-xl hover:-translate-y-1 active:scale-95 transition-all shadow-lg flex items-center justify-center gap-2"
                            >
                                <span>¡Scribirme!</span>
                                <span className="text-xl">→</span>
                            </button>
                        </form>

                        <div className="hidden md:flex border-l border-gray-100 pl-4 items-center justify-center">
                            <WorldIDVerify />
                        </div>
                    </div>

                    <p className="text-[10px] text-gray-400 uppercase tracking-widest font-bold">
                        SIN SPAM • SOLO DULZURA • CANCELA CUANDO QUIERAS
                    </p>
                </div>
            </div>
        </div>
    );
}
