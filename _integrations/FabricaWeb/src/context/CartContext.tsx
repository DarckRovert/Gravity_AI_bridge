"use client";

import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { Product } from '@/data/products';
import { useToast } from './ToastContext';
import { useSound } from './SoundContext';

export interface CartItem extends Product {
    quantity: number;
}

interface CartContextType {
    cart: CartItem[];
    addToCart: (product: Product) => void;
    removeFromCart: (productId: string) => void;
    decrementQuantity: (productId: string) => void;
    clearCart: () => void;
    total: number;
    count: number;
    isOpen: boolean;
    toggleCart: () => void;
}

const CartContext = createContext<CartContextType | undefined>(undefined);

export function CartProvider({ children }: { children: ReactNode }) {
    const [cart, setCart] = useState<CartItem[]>([]);
    const [isOpen, setIsOpen] = useState(false);
    const [isInitialized, setIsInitialized] = useState(false);
    const { showToast } = useToast();
    const { playSound } = useSound();

    // Load from LocalStorage
    useEffect(() => {
        const saved = localStorage.getItem('pastelito_cart');
        if (saved) {
            try {
                setCart(JSON.parse(saved));
            } catch (e) {
                console.error("Failed to load cart", e);
            }
        }
        setIsInitialized(true);
    }, []);

    // Save to LocalStorage
    useEffect(() => {
        if (isInitialized) {
            localStorage.setItem('pastelito_cart', JSON.stringify(cart));
        }
    }, [cart, isInitialized]);

    const addToCart = (product: Product) => {
        setCart(prev => {
            const existing = prev.find(item => item.id === product.id);
            if (existing) {
                return prev.map(item =>
                    item.id === product.id ? { ...item, quantity: item.quantity + 1 } : item
                );
            }
            return [...prev, { ...product, quantity: 1 }];
        });
        showToast(`¡${product.title} agregado al carrito!`, 'success');

        // Sound effect (pop)
        // We can't use useSound here directly because CartProvider is inside SoundProvider?
        // Yes, Layout says SoundProvider wraps CartProvider. So useSound IS available.
        // But we need to get playSound from context first.
        // Wait, I need to add `const { playSound } = useSound();` to CartProvider first.
        setIsOpen(true); // Open cart when adding
    };

    const removeFromCart = (productId: string) => {
        setCart(prev => prev.filter(item => item.id !== productId));
    };

    const decrementQuantity = (productId: string) => {
        setCart(prev => {
            const existing = prev.find(item => item.id === productId);
            if (existing && existing.quantity > 1) {
                return prev.map(item =>
                    item.id === productId ? { ...item, quantity: item.quantity - 1 } : item
                );
            }
            return prev.filter(item => item.id !== productId);
        });
    };

    const clearCart = () => setCart([]);

    const toggleCart = () => setIsOpen(!isOpen);

    const total = cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);
    const count = cart.reduce((sum, item) => sum + item.quantity, 0);

    return (
        <CartContext.Provider value={{ cart, addToCart, removeFromCart, decrementQuantity, clearCart, total, count, isOpen, toggleCart }}>
            {children}
        </CartContext.Provider>
    );
}

export function useCart() {
    const context = useContext(CartContext);
    if (context === undefined) {
        throw new Error('useCart must be used within a CartProvider');
    }
    return context;
}
