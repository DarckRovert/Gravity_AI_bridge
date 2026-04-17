"use client";

import { useState, useEffect, createContext, useContext } from 'react';

type ToastType = 'success' | 'error' | 'info' | 'web3';

interface Toast {
    id: number;
    message: string;
    type: ToastType;
}

interface ToastContextType {
    showToast: (message: string, type?: ToastType) => void;
}

const ToastContext = createContext<ToastContextType | undefined>(undefined);

export function ToastProvider({ children }: { children: React.ReactNode }) {
    const [toasts, setToasts] = useState<Toast[]>([]);

    const showToast = (message: string, type: ToastType = 'info') => {
        const id = Date.now();
        setToasts(prev => [...prev, { id, message, type }]);
        setTimeout(() => {
            setToasts(prev => prev.filter(t => t.id !== id));
        }, 3000);
    };

    return (
        <ToastContext.Provider value={{ showToast }}>
            {children}
            <div className="fixed bottom-6 left-6 z-[110] flex flex-col gap-3">
                {toasts.map(toast => (
                    <div
                        key={toast.id}
                        className={`px-6 py-4 rounded-2xl shadow-2xl text-white font-bold animate-reveal-left flex items-center gap-3 min-w-[300px] border border-white/10 ${toast.type === 'success' ? 'bg-green-600' :
                            toast.type === 'error' ? 'bg-red-600' :
                                toast.type === 'web3' ? 'bg-gradient-to-r from-gray-900 to-black border-amber-400/50 shadow-[0_0_15px_rgba(212,175,55,0.3)]' :
                                    'bg-primary'
                            }`}
                    >
                        <span>{
                            toast.type === 'success' ? '✨' :
                                toast.type === 'error' ? '⚠️' :
                                    toast.type === 'web3' ? '🦊' :
                                        '🔔'
                        }</span>
                        {toast.message}
                    </div>
                ))}
            </div>
        </ToastContext.Provider>
    );
}

export function useToast() {
    const context = useContext(ToastContext);
    if (!context) throw new Error('useToast must be used within a ToastProvider');
    return context;
}
