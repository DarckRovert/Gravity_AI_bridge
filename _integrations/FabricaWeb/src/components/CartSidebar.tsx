"use client";

import { useState, useRef } from 'react';
import { useCart } from '@/context/CartContext';
import Image from 'next/image';
import Link from 'next/link';

export default function CartSidebar() {
    const { cart, isOpen, toggleCart, removeFromCart, decrementQuantity, addToCart, clearCart, total, count } = useCart();
    const [confirmClear, setConfirmClear] = useState(false);

    // Swipe to close logic
    const [touchStart, setTouchStart] = useState<number | null>(null);
    const [touchEnd, setTouchEnd] = useState<number | null>(null);
    const sidebarRef = useRef<HTMLDivElement>(null);

    // Animation state for removing items
    const [removingId, setRemovingId] = useState<string | null>(null);

    const onTouchStart = (e: React.TouchEvent) => {
        setTouchEnd(null);
        setTouchStart(e.targetTouches[0].clientX);
    };

    const onTouchMove = (e: React.TouchEvent) => {
        setTouchEnd(e.targetTouches[0].clientX);

        // Visual feedback during swipe
        if (touchStart && touchEnd && sidebarRef.current) {
            const diff = touchEnd - touchStart;
            if (diff > 0) {
                sidebarRef.current.style.transform = `translateX(${diff}px)`;
            }
        }
    };

    const onTouchEnd = () => {
        if (!touchStart || !touchEnd) return;
        const distance = touchEnd - touchStart;
        const isSwipeRight = distance > 100;

        if (isSwipeRight) {
            toggleCart();
        } else if (sidebarRef.current) {
            sidebarRef.current.style.transform = '';
        }

        setTouchStart(null);
        setTouchEnd(null);
    };

    if (!isOpen) return null;

    return (
        <>
            {/* Overlay */}
            <div
                className="fixed inset-0 bg-black/50 z-[60] backdrop-blur-sm animate-fade-in"
                onClick={toggleCart}
            ></div>

            {/* Sidebar */}
            <div
                ref={sidebarRef}
                className="fixed top-0 right-0 h-full w-full max-w-md bg-white z-[70] shadow-2xl flex flex-col transition-transform duration-200 animate-slide-left"
                role="dialog"
                aria-modal="true"
                aria-label="Carrito de compras"
                onTouchStart={onTouchStart}
                onTouchMove={onTouchMove}
                onTouchEnd={onTouchEnd}
            >
                {/* Header */}
                <div className="p-6 border-b flex justify-between items-center bg-primary text-paper">
                    <h2 className="text-xl font-playfair font-bold flex items-center gap-2">
                        <span>🛒</span> Tu Carrito ({count})
                    </h2>
                    <div className="flex items-center gap-3">
                        {cart.length > 0 && (
                            confirmClear ? (
                                <div className="flex items-center gap-2 text-xs">
                                    <span className="text-amber-300">¿Vaciar?</span>
                                    <button onClick={() => { clearCart(); setConfirmClear(false); }} className="text-red-400 font-bold hover:text-red-300">Sí</button>
                                    <button onClick={() => setConfirmClear(false)} className="text-gray-400 hover:text-white">No</button>
                                </div>
                            ) : (
                                <button onClick={() => setConfirmClear(true)} className="text-xs text-gray-400 hover:text-red-400 transition-colors underline underline-offset-2">Vaciar</button>
                            )
                        )}
                        <button onClick={toggleCart} className="text-2xl hover:text-amber-200 transition-colors" aria-label="Cerrar carrito">✕</button>
                    </div>
                </div>

                {/* Free Delivery Goal */}
                {cart.length > 0 && (
                    <div className="px-6 py-4 bg-secondary/5 border-b border-secondary/10 animate-fade-in">
                        <div className="flex justify-between items-center mb-2">
                            <span className="text-[10px] font-bold text-primary uppercase tracking-wider">Envío Gratis (Zonas Seleccionadas)</span>
                            <span className="text-[10px] font-bold text-secondary">S/ {total.toFixed(2)} / S/ 150</span>
                        </div>
                        <div className="w-full h-2 bg-white rounded-full overflow-hidden border border-secondary/10 p-0.5">
                            <div
                                className="h-full bg-secondary rounded-full transition-all duration-1000 shadow-[0_0_10px_rgba(212,175,55,0.3)]"
                                style={{ width: `${Math.min((total / 150) * 100, 100)}%` }}
                            />
                        </div>
                        {total < 150 ? (
                            <p className="text-[10px] text-gray-400 mt-2 italic">Añade S/ {(150 - total).toFixed(2)} más para envío gratis en Surco y San Borja 🛵</p>
                        ) : (
                            <p className="text-[10px] text-green-600 font-bold mt-2 flex items-center gap-1">
                                <span>✨</span> ¡Envío gratis alcanzado!
                            </p>
                        )}
                    </div>
                )}

                {/* Items list */}
                <div className="flex-1 overflow-y-auto p-6 space-y-6">
                    {cart.length === 0 ? (
                        <div className="h-full flex flex-col items-center justify-center text-center space-y-6 animate-scale-in">
                            <div className="w-40 h-40 bg-gray-50 rounded-full flex items-center justify-center mb-2 shadow-inner">
                                <span className="text-8xl grayscale opacity-30 drop-shadow-lg">🥤</span>
                            </div>
                            <div>
                                <h3 className="text-xl font-bold text-primary mb-2">¡Tu carrito está vacío!</h3>
                                <p className="text-gray-500 italic max-w-[200px] mx-auto">
                                    Parece que aún no te has decidido por ningún postre.
                                </p>
                            </div>
                            <button
                                onClick={toggleCart}
                                className="bg-secondary text-white px-8 py-3 rounded-full font-bold shadow-lg shadow-gray-200 hover:scale-105 transition-all"
                            >
                                Ver la Carta
                            </button>
                        </div>
                    ) : (
                        cart.map((item, idx) => (
                            <div
                                key={item.id}
                                className={`flex gap-4 items-center border-b pb-4 transition-all duration-300 ${item.id === removingId ? 'opacity-0 translate-x-10' : 'animate-fade-up'}`}
                                style={{ animationDelay: `${idx * 0.05}s` }}
                            >
                                <div className="relative w-20 h-20 rounded-lg overflow-hidden flex-shrink-0 border border-gray-100 shadow-sm">
                                    <Image src={item.image} alt={item.title} fill className="object-cover" />
                                </div>
                                <div className="flex-1">
                                    <h3 className="font-bold text-primary text-sm line-clamp-1">{item.title}</h3>
                                    <div className="flex justify-between items-center mt-1">
                                        <p className="text-accent font-bold">S/ {item.price.toFixed(2)}</p>
                                        <div className="flex items-center gap-3 bg-gray-50 rounded-full px-2 py-1 border border-gray-100">
                                            <button
                                                onClick={() => decrementQuantity(item.id)}
                                                className="w-6 h-6 rounded-full flex items-center justify-center hover:bg-white hover:shadow-sm font-bold text-gray-500 transition-all"
                                                aria-label={`Reducir cantidad de ${item.title}`}
                                            >-</button>
                                            <span className="text-sm font-bold w-4 text-center">{item.quantity}</span>
                                            <button
                                                onClick={() => addToCart(item)}
                                                className="w-6 h-6 rounded-full flex items-center justify-center hover:bg-white hover:shadow-sm font-bold text-gray-500 transition-all"
                                                aria-label={`Aumentar cantidad de ${item.title}`}
                                            >+</button>
                                        </div>
                                    </div>
                                    {item.quantity > 1 && (
                                        <p className="text-[10px] text-gray-400 mt-1">Subtotal: <span className="font-bold text-secondary">S/ {(item.price * item.quantity).toFixed(2)}</span></p>
                                    )}
                                </div>
                                <button
                                    onClick={() => {
                                        const id = item.id;
                                        setRemovingId(id);
                                        setTimeout(() => {
                                            removeFromCart(id);
                                            setRemovingId(null);
                                        }, 300);
                                    }}
                                    className="text-gray-300 hover:text-red-500 p-2 transition-colors"
                                    aria-label={`Eliminar ${item.title} del carrito`}
                                >🗑️</button>
                            </div>
                        ))
                    )}
                </div>

                {/* Footer */}
                {cart.length > 0 && (
                    <div className="p-6 border-t bg-gray-50 space-y-4 animate-fade-up">
                        <div className="space-y-2 mb-4">
                            <div className="flex justify-between items-center text-sm text-gray-400">
                                <span>Subtotal</span>
                                <span>S/ {(total / 1.18).toFixed(2)}</span>
                            </div>
                            <div className="flex justify-between items-center text-sm text-gray-400">
                                <span>IGV (18%)</span>
                                <span>S/ {(total - (total / 1.18)).toFixed(2)}</span>
                            </div>
                        </div>
                        <div className="flex justify-between items-center text-lg mt-2 pt-2 border-t border-gray-200">
                            <span className="text-gray-500 font-medium">Total:</span>
                            <span className="text-2xl font-bold text-accent">S/ {total.toFixed(2)}</span>
                        </div>

                        <Link
                            href="/checkout"
                            onClick={toggleCart}
                            className="block w-full bg-primary text-paper text-center py-4 rounded-xl font-bold hover:bg-secondary hover:text-primary transition-all shadow-lg hover:shadow-xl active:scale-95"
                        >
                            FINALIZAR PEDIDO
                        </Link>

                        <p className="text-[10px] text-center text-gray-400 uppercase tracking-widest">
                            * El delivery se calcula al finalizar
                        </p>
                    </div>
                )}
            </div>
        </>
    );
}
