"use client";

import { useState } from 'react';
import Image from 'next/image';
import { Product } from '@/data/products';
import { useCart } from '@/context/CartContext';

export default function ProductCard({ product }: { product: Product }) {
    const { addToCart } = useCart();
    const [isAdded, setIsAdded] = useState(false);
    const [flyPos, setFlyPos] = useState<{ x: number, y: number, dx: number, dy: number } | null>(null);

    const discount = product.originalPrice
        ? Math.round(((product.originalPrice - product.price) / product.originalPrice) * 100)
        : 0;

    const handleAdd = (e: React.MouseEvent) => {
        addToCart(product);
        setIsAdded(true);

        const btn = e.currentTarget.getBoundingClientRect();
        const targetX = window.innerWidth - 60;
        const targetY = 30;

        const dx = targetX - (btn.left + btn.width / 2);
        const dy = targetY - (btn.top + btn.height / 2);

        setFlyPos({ x: btn.left + btn.width / 2, y: btn.top + btn.height / 2, dx, dy });

        setTimeout(() => {
            setIsAdded(false);
            setFlyPos(null);
        }, 800);
    };

    return (
        <div className="bg-white rounded-2xl shadow-md overflow-hidden hover:shadow-xl transition-shadow duration-300 group">
            {/* Image Container */}
            <div className="relative h-64 overflow-hidden">
                {product.image.startsWith('data:') ? (
                    // Admin-uploaded images are stored as base64 data URLs which
                    // cannot be optimized by next/image — native <img> is required here
                    // eslint-disable-next-line @next/next/no-img-element
                    <img
                        src={product.image}
                        alt={product.title}
                        className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                        style={{ objectPosition: product.imagePosition || 'center' }}
                    />
                ) : (
                    // Imagen estática del proyecto
                    <Image
                        src={product.image}
                        alt={product.title}
                        fill
                        className="object-cover group-hover:scale-105 transition-transform duration-500"
                        style={{ objectPosition: product.imagePosition || 'center' }}
                        sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
                    />
                )}

                {/* Chips */}
                <div className="absolute top-4 left-4 flex flex-col gap-2">
                    {product.featured && (
                        <span className="bg-primary text-white text-[10px] font-bold px-3 py-1 rounded-full shadow-lg border border-white/20 flex items-center gap-1">
                            <span>✨</span> Best Seller
                        </span>
                    )}
                    {discount > 0 && (
                        <span className="bg-accent text-white text-[10px] font-bold px-3 py-1 rounded-full shadow-md">
                            -{discount}% OFF
                        </span>
                    )}
                    {product.stock === 'low' && (
                        <span className="bg-amber-500 text-white text-[10px] font-bold px-3 py-1 rounded-full shadow-md animate-pulse">
                            ¡Últimas Unidades!
                        </span>
                    )}
                </div>
            </div>

            {/* Content */}
            <div className="p-6">
                <div className="flex justify-between items-start mb-2">
                    <h3 className="font-fredoka font-bold text-xl text-primary leading-tight">
                        {product.title}
                    </h3>
                </div>

                <p className="text-sm text-gray-500 mb-4 line-clamp-2 min-h-[40px]">
                    {product.description}
                </p>

                <div className="flex items-end justify-between">
                    <div className="flex flex-col">
                        {product.originalPrice && (
                            <span className="text-gray-400 text-sm line-through">
                                S/ {product.originalPrice.toFixed(2)}
                            </span>
                        )}
                        <span className="text-2xl font-bold text-accent">
                            S/ {product.price.toFixed(2)}
                        </span>
                    </div>

                    <button
                        onClick={handleAdd}
                        className={`px-4 py-2 rounded-full font-bold transition-all flex items-center gap-2 shadow-md relative ${isAdded
                            ? 'bg-green-500 text-white scale-110'
                            : 'bg-primary text-paper hover:bg-secondary hover:text-primary hover:scale-105 active:scale-95'
                            }`}
                    >
                        <span>{isAdded ? '¡Añadido! ✨' : 'Agregar'}</span>
                        {!isAdded && <span className="text-lg">+</span>}
                    </button>

                    {/* Flying Ghost */}
                    {flyPos && (
                        <div
                            className="fixed pointer-events-none z-[9999] animate-fly-to-cart"
                            style={{
                                left: flyPos.x - 12,
                                top: flyPos.y - 12,
                                '--target-dx': `${flyPos.dx}px`,
                                '--target-dy': `${flyPos.dy}px`
                            } as any}
                        >
                            <div className="w-8 h-8 bg-secondary rounded-full flex items-center justify-center text-white shadow-xl">
                                🥤
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
