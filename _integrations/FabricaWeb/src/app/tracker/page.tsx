"use client";

import { useState, useEffect, useCallback, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import { getOrderById, FirestoreOrder, ORDER_STATUS_FLOW, OrderStatus } from '@/lib/firebaseOrders';

// Map Firestore statuses to tracker display stages
const STAGES: { status: OrderStatus; label: string; icon: string; color: string }[] = [
    { status: 'nuevo', label: 'Recibido', icon: '📝', color: 'bg-blue-500' },
    { status: 'confirmado', label: 'Confirmado', icon: '✅', color: 'bg-emerald-500' },
    { status: 'preparando', label: 'Preparando', icon: '👨‍🍳', color: 'bg-orange-500' },
    { status: 'enviado', label: 'En Camino', icon: '🛵', color: 'bg-purple-500' },
    { status: 'entregado', label: 'Entregado', icon: '🎉', color: 'bg-green-500' },
];

function TrackerContent() {
    const searchParams = useSearchParams();
    const codeFromUrl = searchParams.get('code') || '';

    const [orderId, setOrderId] = useState(codeFromUrl);
    const [order, setOrder] = useState<FirestoreOrder | null>(null);
    const [currentStage, setCurrentStage] = useState<number | null>(null);
    const [lastUpdate, setLastUpdate] = useState<Date | null>(null);
    const [error, setError] = useState('');
    const [isTracking, setIsTracking] = useState(false);
    const [loading, setLoading] = useState(false);

    const trackOrder = useCallback(async () => {
        const id = orderId.trim();
        if (!id) return;

        setLoading(true);
        setError('');

        const found = await getOrderById(id);

        if (!found) {
            setError('❌ No encontramos ese pedido. Verifica el código.');
            setOrder(null);
            setCurrentStage(null);
            setIsTracking(false);
            setLoading(false);
            return;
        }

        setOrder(found);

        // Find real stage from actual order status
        if (found.status === 'cancelado') {
            setCurrentStage(-1); // Special case
        } else {
            const stageIndex = STAGES.findIndex(s => s.status === found.status);
            setCurrentStage(stageIndex >= 0 ? stageIndex : 0);
        }

        setLastUpdate(new Date());
        setIsTracking(found.status !== 'entregado' && found.status !== 'cancelado');
        setLoading(false);
    }, [orderId]);

    // Auto-track if code comes from URL
    useEffect(() => {
        if (codeFromUrl) {
            setOrderId(codeFromUrl);
            trackOrder();
        }
    }, [codeFromUrl]); // eslint-disable-line react-hooks/exhaustive-deps

    // Auto-refresh every 30s
    useEffect(() => {
        let interval: NodeJS.Timeout;
        if (isTracking) {
            interval = setInterval(() => {
                trackOrder();
            }, 30000);
        }
        return () => clearInterval(interval);
    }, [isTracking, trackOrder]);

    const handleTrackSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        trackOrder();
    };

    const formatDate = (iso: string) => {
        try {
            return new Date(iso).toLocaleDateString('es-PE', {
                day: '2-digit', month: 'short', year: 'numeric',
                hour: '2-digit', minute: '2-digit'
            });
        } catch { return iso; }
    };

    return (
        <main className="min-h-screen bg-dash-bg text-white py-20 px-4 font-poppins relative overflow-hidden">
            {/* Background Decorations */}
            <div className="absolute top-0 left-0 w-full h-full overflow-hidden pointer-events-none">
                <div className="absolute top-[-10%] left-[-10%] w-[50%] h-[50%] bg-secondary/5 rounded-full blur-[100px]"></div>
                <div className="absolute bottom-[-10%] right-[-10%] w-[50%] h-[50%] bg-accent/5 rounded-full blur-[100px]"></div>
            </div>

            <div className="max-w-3xl mx-auto relative z-10">
                <div className="text-center mb-12 animate-fade-in">
                    <h1 className="text-4xl md:text-5xl font-playfair font-bold text-secondary mb-4 drop-shadow-lg">Rastreador de Pedidos</h1>
                    <p className="text-gray-400 text-lg">Ingresa tu código de pedido para ver el estado en tiempo real.</p>
                    {error && <p className="mt-4 text-red-400 font-bold bg-red-900/20 py-2 px-6 rounded-full inline-block animate-bounce border border-red-900/50">{error}</p>}
                </div>

                {/* Input Card */}
                <div className="bg-dash-card/80 backdrop-blur-md border border-dash-border p-8 rounded-3xl shadow-2xl mb-12 animate-fade-up">
                    <form onSubmit={handleTrackSubmit} className="flex flex-col md:flex-row gap-4">
                        <input
                            type="text"
                            value={orderId}
                            onChange={(e) => setOrderId(e.target.value)}
                            placeholder="Ej: DM-20260220-A3F2"
                            className="flex-1 bg-dash-bg/50 border border-dash-border rounded-xl px-6 py-4 text-center tracking-[0.2em] text-xl font-mono focus:outline-none focus:border-secondary transition-all uppercase placeholder:normal-case placeholder:tracking-normal"
                        />
                        <button
                            type="submit"
                            disabled={loading}
                            className="bg-secondary text-dash-bg px-10 py-4 rounded-xl font-bold text-lg hover:bg-white hover:shadow-[0_0_20px_rgba(212,175,55,0.6)] transition-all transform hover:-translate-y-1 active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            {loading ? '🔍...' : 'RASTREAR'}
                        </button>
                    </form>
                </div>

                {/* Cancelled Order */}
                {currentStage === -1 && order && (
                    <div className="bg-red-900/20 border border-red-800/50 rounded-3xl p-8 text-center animate-fade-up">
                        <div className="text-5xl mb-4">❌</div>
                        <h2 className="text-2xl font-playfair text-red-400 mb-2">Pedido Cancelado</h2>
                        <p className="text-gray-400">El pedido <strong className="text-white font-mono">{order.id}</strong> fue cancelado.</p>
                        <p className="text-gray-500 text-sm mt-2">Última actualización: {formatDate(order.updatedAt)}</p>
                    </div>
                )}

                {/* Results Timeline — Real Status */}
                {currentStage !== null && currentStage >= 0 && order && (
                    <div className="space-y-8 animate-fade-up" style={{ animationDelay: '0.2s' }}>
                        {/* Stage Card */}
                        <div className="bg-dash-card/90 backdrop-blur-xl border border-dash-border p-8 md:p-10 rounded-3xl shadow-2xl relative overflow-hidden">

                            <div className="flex justify-between items-center mb-10 border-b border-dash-border pb-4">
                                <div>
                                    <h2 className="text-2xl font-playfair text-secondary">
                                        {STAGES[currentStage].label}
                                    </h2>
                                    <p className="text-xs text-gray-500 mt-1 flex items-center gap-2">
                                        <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
                                        Actualizado: {lastUpdate?.toLocaleTimeString()}
                                    </p>
                                </div>
                                <div className="text-4xl animate-bounce">
                                    {STAGES[currentStage].icon}
                                </div>
                            </div>

                            {/* Progress Bar */}
                            <div className="relative mb-12 px-2">
                                <div className="absolute top-1/2 left-0 w-full h-1 bg-gray-700 rounded-full -translate-y-1/2"></div>
                                <div
                                    className="absolute top-1/2 left-0 h-1 bg-gradient-to-r from-secondary to-accent rounded-full -translate-y-1/2 transition-all duration-1000 ease-out"
                                    style={{ width: `${(currentStage / (STAGES.length - 1)) * 100}%` }}
                                ></div>

                                <div className="relative flex justify-between z-10">
                                    {STAGES.map((stage, idx) => {
                                        const isActive = idx <= currentStage;
                                        const isCurrent = idx === currentStage;

                                        return (
                                            <div key={idx} className="flex flex-col items-center gap-2 w-10">
                                                <div className={`w-10 h-10 rounded-full flex items-center justify-center text-sm border-4 transition-all duration-500 ${isActive
                                                    ? 'bg-dash-bg border-secondary shadow-[0_0_15px_rgba(212,175,55,0.5)] scale-110'
                                                    : 'bg-gray-800 border-gray-600 grayscale'
                                                    }`}>
                                                    {isActive ? stage.icon : ''}
                                                </div>
                                                <p className={`absolute -bottom-8 whitespace-nowrap text-[10px] md:text-xs font-bold transition-colors duration-300 ${isCurrent ? 'text-secondary scale-110' : isActive ? 'text-gray-300' : 'text-gray-600'
                                                    }`}>
                                                    {stage.label}
                                                </p>
                                            </div>
                                        );
                                    })}
                                </div>
                            </div>
                        </div>

                        {/* Order Details */}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            {/* Order Info Card */}
                            <div className="bg-dash-card/80 border border-dash-border rounded-3xl p-6 shadow-lg">
                                <h3 className="text-secondary text-sm font-bold uppercase tracking-widest mb-4">📋 Detalle</h3>
                                <div className="space-y-3 text-sm">
                                    <div className="flex justify-between">
                                        <span className="text-gray-400">Código</span>
                                        <span className="font-mono font-bold">{order.id}</span>
                                    </div>
                                    <div className="flex justify-between">
                                        <span className="text-gray-400">Cliente</span>
                                        <span>{order.customer}</span>
                                    </div>
                                    <div className="flex justify-between">
                                        <span className="text-gray-400">Entrega</span>
                                        <span>{order.deliveryDate} - {order.deliveryTime}</span>
                                    </div>
                                    <div className="flex justify-between">
                                        <span className="text-gray-400">Zona</span>
                                        <span>{order.deliveryZone || 'No especificada'}</span>
                                    </div>
                                    <hr className="border-dash-border" />
                                    <div className="flex justify-between">
                                        <span className="text-gray-400">Productos</span>
                                        <span>{order.items?.length || 0} items</span>
                                    </div>
                                    <div className="flex justify-between text-lg font-bold">
                                        <span className="text-secondary">Total</span>
                                        <span className="text-secondary">S/ {(order.total || 0).toFixed(2)}</span>
                                    </div>
                                </div>
                            </div>

                            {/* Status Timeline Card */}
                            <div className="bg-gradient-to-br from-secondary/20 to-accent/20 border border-secondary/30 rounded-3xl p-6 flex flex-col items-center justify-center text-center">
                                <p className="text-secondary text-sm font-bold uppercase tracking-widest mb-2">
                                    {order.status === 'entregado' ? '🎉 Entregado' : '⏳ Estado Actual'}
                                </p>
                                <p className="text-5xl mb-3">
                                    {STAGES[currentStage].icon}
                                </p>
                                <p className="text-2xl font-bold text-white mb-1">
                                    {STAGES[currentStage].label}
                                </p>
                                <p className="text-xs text-gray-400">
                                    Última actualización: {formatDate(order.updatedAt)}
                                </p>
                                {isTracking && (
                                    <p className="text-[10px] text-gray-500 mt-3 flex items-center gap-1">
                                        <span className="w-1.5 h-1.5 bg-green-400 rounded-full animate-pulse" />
                                        Se actualiza cada 30 segundos
                                    </p>
                                )}
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </main>
    );
}

export default function TrackerPage() {
    return (
        <Suspense fallback={
            <main className="min-h-screen bg-dash-bg text-white flex items-center justify-center">
                <div className="animate-pulse text-2xl">🔍 Cargando tracker...</div>
            </main>
        }>
            <TrackerContent />
        </Suspense>
    );
}
