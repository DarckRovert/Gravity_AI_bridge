"use client";

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useContent, useTheme } from '@/context/SiteConfigContext';
import { useCart } from '@/context/CartContext';
import { useSound } from '@/context/SoundContext';
import dynamic from 'next/dynamic';

// Removed WalletConnect as part of Web3 removal

export default function Navbar() {
    const [isOpen, setIsOpen] = useState(false);
    const [points, setPoints] = useState(0);
    const [isScrolled, setIsScrolled] = useState(false);
    const [bump, setBump] = useState(false);

    const pathname = usePathname();
    const { content } = useContent();
    const { theme, setTheme } = useTheme();
    const { count, toggleCart } = useCart();
    const { muted, toggleMute } = useSound();

    useEffect(() => {
        const savedPoints = localStorage.getItem('pastelito_points');
        if (savedPoints) setPoints(parseInt(savedPoints));

        const handleScroll = () => {
            setIsScrolled(window.scrollY > 50);
        };

        window.addEventListener('scroll', handleScroll);
        return () => window.removeEventListener('scroll', handleScroll);
    }, []);

    useEffect(() => {
        if (count > 0) {
            setBump(true);
            const timer = setTimeout(() => setBump(false), 300);
            return () => clearTimeout(timer);
        }
    }, [count]);

    const navLinks = [
        { label: 'Inicio', href: '/' },
        { label: 'Carta', href: '/menu' },
        { label: 'Crea tu Torta', href: '/builder' },
        { label: 'Nosotros', href: '/#nosotros' },
        { label: 'Rastrear', href: '/tracker' },
        { label: 'Opiniones', href: '/feedback' },
    ];

    const toggleTheme = () => {
        setTheme({ darkMode: !theme.darkMode });
    };

    return (
        <header
            className={`fixed w-full top-0 z-50 glass-header text-primary shadow-sm font-nunito transition-all duration-300 border-b border-primary/10 
            ${isScrolled ? 'py-0' : 'py-2'}`}
        >
            <nav className={`container mx-auto px-4 flex items-center justify-between transition-all duration-300 ${isScrolled ? 'h-16' : 'h-20'}`}>
                {/* Logo */}
                <Link href="/" className="flex items-center gap-1.5 sm:gap-3 font-fredoka font-bold text-lg sm:text-xl md:text-2xl hover:text-secondary transition-all group min-w-0">
                    <span className="text-xl sm:text-2xl md:text-3xl group-hover:rotate-12 transition-transform flex-shrink-0">🍍</span>
                    <span className="hidden xs:inline sm:inline truncate max-w-[120px] sm:max-w-none">{content.businessName}</span>
                </Link>

                {/* Desktop Menu */}
                <ul className="hidden lg:flex items-center gap-6 xl:gap-8 font-medium text-[10px] xl:text-xs uppercase tracking-widest">
                    {navLinks.map(link => (
                        <li key={link.href}>
                            <Link
                                href={link.href}
                                className={`hover:text-secondary transition-colors relative py-1 ${pathname === link.href ? 'text-secondary after:w-full' : 'after:w-0'} after:content-[''] after:absolute after:bottom-0 after:left-0 after:h-0.5 after:bg-secondary after:transition-all`}
                            >
                                {link.label}
                            </Link>
                        </li>
                    ))}

                    {/* Points Display */}
                    <li className="bg-secondary/10 px-4 py-2 rounded-full flex items-center gap-2 border border-secondary/20 shadow-inner">
                        <span className="text-base">🍬</span>
                        <span className="font-bold text-secondary">{points}</span>
                        <span className="opacity-60 text-[10px] text-primary">Pts</span>
                    </li>

                    {/* Web3 Removed */}
                </ul>

                {/* Actions */}
                <div className="flex items-center gap-4 text-primary">

                    <button
                        onClick={toggleTheme}
                        className="text-xl hover:scale-110 transition-transform hidden sm:block w-10 h-10 rounded-full bg-primary/5 flex items-center justify-center hover:bg-primary/10"
                        title={theme.darkMode ? "Modo Claro" : "Modo Oscuro"}
                    >
                        {theme.darkMode ? '☀️' : '🌙'}
                    </button>

                    <button
                        onClick={toggleMute}
                        className="text-xl hover:scale-110 transition-transform hidden sm:block w-10 h-10 rounded-full bg-primary/5 flex items-center justify-center hover:bg-primary/10"
                        title={muted ? "Activar Sonido" : "Silenciar"}
                    >
                        {muted ? '🔇' : '🔊'}
                    </button>

                    {/* Cart Button */}
                    <button
                        onClick={toggleCart}
                        className={`relative w-9 h-9 sm:w-10 sm:h-10 flex items-center justify-center rounded-full hover:bg-primary/5 transition-all ${bump ? 'scale-125' : ''}`}
                    >
                        <span className="text-xl sm:text-2xl">🛒</span>
                        {count > 0 && (
                            <span className="absolute -top-1 -right-1 bg-accent text-white text-[9px] sm:text-[10px] font-bold w-4 h-4 sm:w-5 sm:h-5 flex items-center justify-center rounded-full shadow-md animate-scale-in">
                                {count > 9 ? '9+' : count}
                            </span>
                        )}
                    </button>

                    {/* Mobile Toggle */}
                    <button
                        className="lg:hidden p-2 text-3xl"
                        onClick={() => setIsOpen(!isOpen)}
                    >
                        {isOpen ? '✕' : '☰'}
                    </button>
                </div>
            </nav>

            {/* Mobile Menu */}
            {isOpen && (
                <div className="lg:hidden fixed inset-0 top-[64px] z-40 animate-fade-in bg-white/95 backdrop-blur-xl">
                    <div className="container mx-auto px-6 py-10 flex flex-col h-[calc(100vh-64px)] overflow-y-auto">
                        <ul className="space-y-6 font-fredoka font-bold text-2xl text-primary">
                            {navLinks.map((link, idx) => (
                                <li key={link.href} className="animate-fade-up" style={{ animationDelay: `${idx * 0.1}s` }}>
                                    <Link
                                        href={link.href}
                                        onClick={() => setIsOpen(false)}
                                        className={`flex items-center justify-between group ${pathname === link.href ? 'text-secondary' : ''}`}
                                    >
                                        <span>{link.label}</span>
                                        <span className="text-secondary opacity-0 group-hover:opacity-100 transition-opacity">→</span>
                                    </Link>
                                </li>
                            ))}
                        </ul>

                        <div className="mt-auto space-y-8 pt-10 border-t border-primary/5">
                            {/* Points Mobile */}
                            <div className="flex items-center justify-between p-4 bg-secondary/5 rounded-2xl border border-secondary/10">
                                <div className="flex items-center gap-3">
                                    <span className="text-2xl">🍬</span>
                                    <span className="font-bold text-primary">Tus Puntos Antojín</span>
                                </div>
                                <span className="font-mono font-bold text-xl text-secondary">{points}</span>
                            </div>

                            {/* Controls Mobile */}
                            <div className="grid grid-cols-2 gap-4">
                                <button
                                    onClick={toggleTheme}
                                    className="flex items-center justify-center gap-3 p-4 bg-gray-50 rounded-2xl font-bold text-sm text-primary active:scale-95 transition-all"
                                >
                                    {theme.darkMode ? '☀️ Modo Claro' : '🌙 Modo Oscuro'}
                                </button>
                                <button
                                    onClick={toggleMute}
                                    className="flex items-center justify-center gap-3 p-4 bg-gray-50 rounded-2xl font-bold text-sm text-primary active:scale-95 transition-all"
                                >
                                    {muted ? '🔇 Activar Sonido' : '🔊 Silenciar'}
                                </button>
                            </div>

                            {/* Web3 Removed */}
                        </div>
                    </div>
                </div>
            )}
        </header >
    );
}
