"use client";

import { useCoupons } from '@/context/SiteConfigContext';
import { useState } from 'react';

interface CouponManagerProps {
    onToast?: (msg: string, type: 'success' | 'error') => void;
}

export function CouponManager({ onToast }: CouponManagerProps) {
    const { coupons, addCoupon, removeCoupon } = useCoupons();
    const [showForm, setShowForm] = useState(false);
    const [newCode, setNewCode] = useState('');
    const [newDiscount, setNewDiscount] = useState('10');
    const [newType, setNewType] = useState<'percent' | 'fixed'>('percent');

    const handleCreate = () => {
        const code = newCode.trim().toUpperCase();
        if (!code) { onToast?.('Ingresa un código', 'error'); return; }
        if (coupons.some(c => c.code === code)) { onToast?.('Código ya existe', 'error'); return; }

        const discount = parseFloat(newDiscount);
        if (isNaN(discount) || discount <= 0) { onToast?.('Descuento inválido', 'error'); return; }

        addCoupon({
            code,
            discount,
            type: newType,
            active: true,
        });

        onToast?.(`Cupón ${code} creado (${discount}${newType === 'percent' ? '%' : ' soles'})`, 'success');
        setNewCode('');
        setNewDiscount('10');
        setShowForm(false);
    };

    const handleToggle = (coupon: typeof coupons[0]) => {
        // addCoupon does upsert (filters by code then adds) — so we can toggle active
        addCoupon({ ...coupon, active: !coupon.active });
        onToast?.(`${coupon.code} → ${coupon.active ? '⏸️ Desactivado' : '✅ Activado'}`, 'success');
    };

    const handleDelete = (code: string) => {
        removeCoupon(code);
        onToast?.(`Cupón ${code} eliminado`, 'success');
    };

    return (
        <div className="bg-dash-card border border-dash-border rounded-2xl p-6">
            <div className="flex justify-between items-center mb-6">
                <h2 className="text-xl font-playfair font-bold text-secondary">🏷️ Gestión de Cupones</h2>
                <button
                    onClick={() => setShowForm(!showForm)}
                    className="bg-secondary/20 text-secondary px-3 py-1.5 rounded-lg text-sm font-medium hover:bg-secondary/30 transition-all"
                >
                    {showForm ? '✕ Cerrar' : '+ Nuevo Cupón'}
                </button>
            </div>

            {/* Create Form */}
            {showForm && (
                <div className="bg-dash-bg/50 border border-dash-border/50 rounded-xl p-4 mb-4 space-y-3">
                    <div className="grid grid-cols-3 gap-3">
                        <input
                            type="text"
                            placeholder="CÓDIGO"
                            value={newCode}
                            onChange={e => setNewCode(e.target.value.toUpperCase())}
                            className="bg-dash-bg border border-dash-border rounded-lg px-3 py-2 text-white text-sm uppercase tracking-wider focus:outline-none focus:border-secondary"
                        />
                        <input
                            type="number"
                            placeholder="Descuento"
                            value={newDiscount}
                            onChange={e => setNewDiscount(e.target.value)}
                            className="bg-dash-bg border border-dash-border rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-secondary"
                        />
                        <select
                            value={newType}
                            onChange={e => setNewType(e.target.value as 'percent' | 'fixed')}
                            className="bg-dash-bg border border-dash-border rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-secondary"
                        >
                            <option value="percent">% Porcentaje</option>
                            <option value="fixed">S/ Fijo</option>
                        </select>
                    </div>
                    <button
                        onClick={handleCreate}
                        className="w-full bg-secondary text-dash-bg py-2 rounded-lg text-sm font-bold hover:bg-white transition-all"
                    >
                        Crear Cupón
                    </button>
                </div>
            )}

            {/* Coupon List */}
            <div className="space-y-2 max-h-[350px] overflow-y-auto" style={{ scrollbarWidth: 'thin' }}>
                {coupons.length === 0 && (
                    <p className="text-center text-dash-border py-8">No hay cupones creados</p>
                )}
                {coupons.map(coupon => (
                    <div key={coupon.code} className="flex items-center justify-between bg-dash-bg/50 rounded-xl p-3 border border-dash-border/50 group">
                        <div className="flex items-center gap-3">
                            <span className={`font-mono text-sm font-bold tracking-wider ${coupon.active ? 'text-secondary' : 'text-dash-border line-through'}`}>
                                {coupon.code}
                            </span>
                            <span className="text-white text-sm">
                                {coupon.discount}{coupon.type === 'percent' ? '%' : ' soles'}
                            </span>
                        </div>
                        <div className="flex items-center gap-2">
                            {/* Toggle Switch */}
                            <button
                                onClick={() => handleToggle(coupon)}
                                className={`w-10 h-5 rounded-full transition-all relative ${coupon.active ? 'bg-green-600' : 'bg-dash-border/30'}`}
                                title={coupon.active ? 'Desactivar' : 'Activar'}
                            >
                                <span className={`absolute w-4 h-4 bg-white rounded-full top-0.5 transition-all ${coupon.active ? 'left-5' : 'left-0.5'}`} />
                            </button>
                            <button
                                onClick={() => handleDelete(coupon.code)}
                                className="text-red-400 hover:text-red-300 text-xs opacity-0 group-hover:opacity-100 transition-opacity"
                            >
                                🗑️
                            </button>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}
