"use client";

import { useState } from 'react';
import { connectWallet, WalletState } from '@/lib/web3';
import { useToast } from '@/context/ToastContext';

export default function WalletConnect() {
    const [wallet, setWallet] = useState<WalletState>({
        address: null,
        balance: null,
        chainId: null,
        isConnected: false
    });
    const [loading, setLoading] = useState(false);

    const { showToast } = useToast();

    const handleConnect = async () => {
        setLoading(true);
        try {
            const data = await connectWallet();
            setWallet(data);
            localStorage.setItem('wallet_connected', 'true');
            showToast("Wallet Conectada Exitosamente", 'web3');
        } catch (error: unknown) {
            const message = error instanceof Error ? error.message : "Error conectando wallet";
            alert(message);
        } finally {
            setLoading(false);
        }
    };

    if (wallet.isConnected && wallet.address) {
        return (
            <div className="group relative flex items-center gap-3 bg-white/10 border border-white/20 rounded-xl px-4 py-2 backdrop-blur-md shadow-[0_0_20px_rgba(212,175,55,0.15)] hover:shadow-[0_0_30px_rgba(194,24,91,0.3)] transition-all duration-500 cursor-pointer overflow-hidden animate-fade-in">
                {/* Neon Glow Background */}
                <div className="absolute inset-0 bg-gradient-to-r from-secondary/10 via-accent/10 to-secondary/10 opacity-0 group-hover:opacity-100 transition-opacity duration-500" />

                {/* Status Dot */}
                <div className="relative">
                    <div className="w-2.5 h-2.5 rounded-full bg-green-400 shadow-[0_0_10px_#4ade80] animate-pulse" />
                </div>

                {/* Address & Network */}
                <div className="flex flex-col items-start leading-none z-10">
                    <span className="text-[10px] text-primary/60 font-mono tracking-wider">POLYGON</span>
                    <span className="text-xs font-bold font-mono text-primary/80 group-hover:text-accent transition-colors">
                        {wallet.address.slice(0, 6)}...{wallet.address.slice(-4)}
                    </span>
                </div>

                {/* Divider */}
                <div className="h-6 w-[1px] bg-gradient-to-b from-transparent via-primary/20 to-transparent" />

                {/* Balance */}
                <div className="flex items-center gap-1 z-10">
                    <span className="text-sm font-bold bg-gradient-to-r from-secondary to-accent bg-clip-text text-transparent group-hover:scale-110 transition-transform">
                        {wallet.balance}
                    </span>
                    <span className="text-[10px] text-primary/60 font-bold">$DULCE</span>
                </div>
            </div>
        );
    }

    return (
        <button
            onClick={handleConnect}
            disabled={loading}
            className={`
                group relative px-6 py-2.5 rounded-xl font-bold text-xs tracking-widest uppercase transition-all duration-300
                bg-gradient-to-r from-primary to-accent text-white
                shadow-[0_0_20px_rgba(78,52,46,0.3)] hover:shadow-[0_0_30px_rgba(194,24,91,0.6)]
                hover:scale-105 active:scale-95 border border-white/10
                overflow-hidden
                ${loading ? 'opacity-70 cursor-wait' : ''}
            `}
        >
            {/* Shimmer Effect */}
            <div className="absolute top-0 -left-full w-full h-full bg-gradient-to-r from-transparent via-white/30 to-transparent skew-x-12 group-hover:animate-[shimmer_1s_infinite]" />

            <span className="relative z-10 flex items-center gap-2">
                {loading ? (
                    <>
                        <span className="animate-spin text-lg">⚙️</span>
                        <span>Sincronizando...</span>
                    </>
                ) : (
                    <>
                        <span className="text-lg group-hover:rotate-12 transition-transform">🦊</span>
                        <span>Conectar Wallet</span>
                    </>
                )}
            </span>
        </button>
    );
}
