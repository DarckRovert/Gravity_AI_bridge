"use client";

/**
 * 📦 Order Pipeline — Dashboard Component
 * 
 * Visual pipeline for managing order statuses.
 * Supports: Nuevo → Confirmado → Preparando → Enviado → Entregado
 */

import { useState, useEffect } from 'react';
import {
    FirestoreOrder, OrderStatus, ORDER_STATUS_FLOW,
    getOrders, updateOrderStatus, subscribeToOrders
} from '@/lib/firebaseOrders';
import { isFirebaseConfigured, getDataSource } from '@/lib/firebase';

interface OrderPipelineProps {
    onToast?: (msg: string, type: 'success' | 'error') => void;
}

export function OrderPipeline({ onToast }: OrderPipelineProps) {
    const [orders, setOrders] = useState<FirestoreOrder[]>([]);
    const [loading, setLoading] = useState(true);
    const [activeStatus, setActiveStatus] = useState<OrderStatus | 'todos'>('todos');
    const [expandedId, setExpandedId] = useState<string | null>(null);

    useEffect(() => {
        // Try real-time subscription first, fallback to one-time load
        const unsub = subscribeToOrders((fetchedOrders) => {
            setOrders(fetchedOrders);
            setLoading(false);
        });

        // If no subscription (localStorage mode), load once
        if (unsub === null) {
            getOrders().then(fetchedOrders => {
                setOrders(fetchedOrders);
                setLoading(false);
            });
        }

        return () => {
            if (unsub) unsub();
        };
    }, []);

    const handleStatusChange = async (orderId: string, newStatus: OrderStatus) => {
        const success = await updateOrderStatus(orderId, newStatus);
        if (success) {
            // Update local state immediately
            setOrders(prev => prev.map(o =>
                o.id === orderId ? { ...o, status: newStatus, updatedAt: new Date().toISOString() } : o
            ));
            const statusInfo = ORDER_STATUS_FLOW.find(s => s.status === newStatus);
            onToast?.(`${statusInfo?.icon} Pedido ${orderId} → ${statusInfo?.label}`, 'success');
        } else {
            onToast?.(`Error al actualizar pedido ${orderId}`, 'error');
        }
    };

    const filteredOrders = activeStatus === 'todos'
        ? orders
        : orders.filter(o => o.status === activeStatus);

    // Count by status
    const statusCounts: Record<string, number> = {};
    ORDER_STATUS_FLOW.forEach(s => {
        statusCounts[s.status] = orders.filter(o => o.status === s.status).length;
    });

    const dataSource = getDataSource();
    const formatPrice = (n: number) => `S/ ${n.toFixed(2)}`;
    const formatDate = (iso: string) => {
        try {
            const d = new Date(iso);
            return d.toLocaleDateString('es-PE', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' });
        } catch { return iso; }
    };

    if (loading) {
        return (
            <div className="bg-dash-card border border-dash-border rounded-2xl p-8 text-center">
                <div className="animate-pulse text-2xl mb-2">📦</div>
                <p className="text-dash-border">Cargando pedidos...</p>
            </div>
        );
    }

    return (
        <div className="space-y-4">
            {/* Data Source Indicator */}
            <div className="flex items-center justify-between">
                <h2 className="text-xl font-playfair font-bold text-secondary">📦 Pipeline de Pedidos</h2>
                <div className="flex items-center gap-2">
                    <span className={`w-2 h-2 rounded-full ${dataSource === 'firebase' ? 'bg-green-400' : 'bg-amber-400'}`} />
                    <span className="text-dash-border text-xs">
                        {dataSource === 'firebase' ? '🔥 Firebase (Real-time)' : '💾 Local (navegador)'}
                    </span>
                </div>
            </div>

            {/* Status Filter Pills */}
            <div className="flex gap-2 overflow-x-auto pb-2">
                <button
                    onClick={() => setActiveStatus('todos')}
                    className={`px-3 py-1.5 rounded-lg text-sm font-medium whitespace-nowrap transition-all ${activeStatus === 'todos'
                        ? 'bg-secondary text-dash-bg'
                        : 'bg-dash-bg text-dash-border hover:bg-dash-border/20'
                        }`}
                >
                    Todos ({orders.length})
                </button>
                {ORDER_STATUS_FLOW.map(s => (
                    <button
                        key={s.status}
                        onClick={() => setActiveStatus(s.status)}
                        className={`px-3 py-1.5 rounded-lg text-sm font-medium whitespace-nowrap transition-all ${activeStatus === s.status
                            ? 'bg-secondary text-dash-bg'
                            : 'bg-dash-bg text-dash-border hover:bg-dash-border/20'
                            }`}
                    >
                        {s.icon} {s.label} ({statusCounts[s.status] || 0})
                    </button>
                ))}
            </div>

            {/* Orders List */}
            <div className="space-y-3 max-h-[600px] overflow-y-auto pr-1" style={{ scrollbarWidth: 'thin' }}>
                {filteredOrders.length === 0 && (
                    <div className="bg-dash-card border border-dash-border rounded-2xl p-8 text-center">
                        <div className="text-3xl mb-2">📭</div>
                        <p className="text-dash-border">
                            {activeStatus === 'todos' ? 'No hay pedidos aún' : `No hay pedidos con estado "${activeStatus}"`}
                        </p>
                    </div>
                )}

                {filteredOrders.map(order => {
                    const currentFlow = ORDER_STATUS_FLOW.find(s => s.status === order.status);
                    const currentIndex = ORDER_STATUS_FLOW.findIndex(s => s.status === order.status);
                    const isExpanded = expandedId === order.id;
                    const nextStatuses = ORDER_STATUS_FLOW.filter((_, i) =>
                        i > currentIndex && i < ORDER_STATUS_FLOW.length - 1 // exclude 'cancelado' from next
                    );

                    return (
                        <div
                            key={order.id}
                            className="bg-dash-card border border-dash-border rounded-2xl overflow-hidden hover:border-secondary/30 transition-all"
                        >
                            {/* Order Header */}
                            <div
                                className="flex items-center gap-4 p-4 cursor-pointer"
                                onClick={() => setExpandedId(isExpanded ? null : order.id)}
                            >
                                {/* Status Badge */}
                                <div
                                    className="w-10 h-10 rounded-full flex items-center justify-center text-lg flex-shrink-0"
                                    style={{ backgroundColor: `${currentFlow?.color}20` }}
                                >
                                    {currentFlow?.icon}
                                </div>

                                {/* Order Info */}
                                <div className="flex-1 min-w-0">
                                    <div className="flex items-center gap-2">
                                        <span className="text-white font-mono text-sm font-bold">{order.id}</span>
                                        <span
                                            className="text-[10px] px-2 py-0.5 rounded-full font-medium"
                                            style={{
                                                backgroundColor: `${currentFlow?.color}20`,
                                                color: currentFlow?.color
                                            }}
                                        >
                                            {currentFlow?.label}
                                        </span>
                                    </div>
                                    <div className="flex items-center gap-3 mt-0.5">
                                        <span className="text-dash-border text-xs">{order.customer}</span>
                                        <span className="text-dash-border text-xs">•</span>
                                        <span className="text-dash-border text-xs">{formatDate(order.createdAt)}</span>
                                    </div>
                                </div>

                                {/* Total */}
                                <div className="text-right flex-shrink-0">
                                    <span className="text-secondary font-bold">{formatPrice(order.total || 0)}</span>
                                    <span className="text-dash-border text-xs block">{order.paymentMethod}</span>
                                </div>

                                {/* Expand Arrow */}
                                <span className={`text-dash-border text-xs transition-transform ${isExpanded ? 'rotate-180' : ''}`}>
                                    ▼
                                </span>
                            </div>

                            {/* Expanded Details */}
                            {isExpanded && (
                                <div className="border-t border-dash-border/50 p-4 space-y-4">
                                    {/* Items */}
                                    <div>
                                        <p className="text-xs text-dash-border uppercase tracking-wider mb-2">Productos</p>
                                        <div className="space-y-1">
                                            {order.items?.map((item, i) => (
                                                <div key={i} className="flex justify-between text-sm">
                                                    <span className="text-white">{item.quantity}x {item.title}</span>
                                                    <span className="text-dash-border">{formatPrice((item.price || 0) * item.quantity)}</span>
                                                </div>
                                            ))}
                                        </div>
                                    </div>

                                    {/* Customer Details */}
                                    <div className="grid grid-cols-2 gap-3">
                                        <div>
                                            <p className="text-xs text-dash-border">📞 Teléfono</p>
                                            <p className="text-white text-sm">{order.phone}</p>
                                        </div>
                                        <div>
                                            <p className="text-xs text-dash-border">📍 Dirección</p>
                                            <p className="text-white text-sm">{order.address}</p>
                                        </div>
                                        <div>
                                            <p className="text-xs text-dash-border">📅 Entrega</p>
                                            <p className="text-white text-sm">{order.deliveryDate} - {order.deliveryTime}</p>
                                        </div>
                                        <div>
                                            <p className="text-xs text-dash-border">🛵 Zona</p>
                                            <p className="text-white text-sm">{order.deliveryZone || 'No especificada'}</p>
                                        </div>
                                    </div>

                                    {order.notes && (
                                        <div>
                                            <p className="text-xs text-dash-border">📝 Notas</p>
                                            <p className="text-white text-sm italic">{order.notes}</p>
                                        </div>
                                    )}

                                    {order.isGift && (
                                        <div className="bg-pink-900/20 border border-pink-800/30 rounded-xl p-3">
                                            <p className="text-xs text-pink-400 font-medium mb-1">🎁 Pedido de Regalo</p>
                                            <p className="text-sm text-white">Para: {order.giftTo} | De: {order.giftFrom}</p>
                                            {order.giftMessage && <p className="text-sm text-dash-border italic mt-1">&quot;{order.giftMessage}&quot;</p>}
                                        </div>
                                    )}

                                    {/* Status Actions */}
                                    <div>
                                        <p className="text-xs text-dash-border uppercase tracking-wider mb-2">Cambiar Estado</p>
                                        <div className="flex flex-wrap gap-2">
                                            {nextStatuses.map(ns => (
                                                <button
                                                    key={ns.status}
                                                    onClick={() => handleStatusChange(order.id, ns.status)}
                                                    className="px-3 py-1.5 rounded-lg text-sm font-medium transition-all hover:scale-105"
                                                    style={{
                                                        backgroundColor: `${ns.color}20`,
                                                        color: ns.color,
                                                    }}
                                                >
                                                    {ns.icon} {ns.label}
                                                </button>
                                            ))}
                                            {order.status !== 'cancelado' && order.status !== 'entregado' && (
                                                <button
                                                    onClick={() => handleStatusChange(order.id, 'cancelado')}
                                                    className="px-3 py-1.5 rounded-lg text-sm font-medium bg-red-900/20 text-red-400 hover:bg-red-900/40 transition-all"
                                                >
                                                    ❌ Cancelar
                                                </button>
                                            )}
                                        </div>
                                    </div>

                                    {/* WhatsApp Quick Action */}
                                    <button
                                        onClick={() => {
                                            const msg = `Hola ${order.customer}! 🍰 Tu pedido *${order.id}* está ahora: *${currentFlow?.icon} ${currentFlow?.label}*. ¡Gracias por tu compra!`;
                                            window.open(`https://wa.me/51${order.phone?.replace(/\D/g, '')}?text=${encodeURIComponent(msg)}`, '_blank');
                                        }}
                                        className="w-full bg-green-900/20 text-green-400 py-2 rounded-lg text-sm font-medium hover:bg-green-900/30 transition-all"
                                    >
                                        💬 Notificar por WhatsApp
                                    </button>
                                </div>
                            )}
                        </div>
                    );
                })}
            </div>
        </div>
    );
}
