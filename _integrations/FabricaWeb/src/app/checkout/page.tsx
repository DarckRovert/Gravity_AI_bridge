"use client";

import { useCart } from '@/context/CartContext';
import { useToast } from '@/context/ToastContext';
import { useCoupons, useContent, useLayout } from '@/context/SiteConfigContext';
import { useSound } from '@/context/SoundContext';
import { useState } from 'react';
import { useRouter } from 'next/navigation';

import { sanitizeInput, validatePeruvianPhone } from '@/lib/security';
import { generateWhatsAppLink } from '@/lib/whatsappEngine';
import { createOrder } from '@/lib/firebaseOrders';
import { earnPoints, getRedeemableDiscount, redeemPoints } from '@/lib/loyaltyPoints';
import { openCulqiModal, isCulqiConfigured } from '@/lib/culqi';

export default function CheckoutPage() {
    const { cart, total, clearCart } = useCart();
    const { content } = useContent();
    const { layout } = useLayout();
    const { showToast } = useToast();
    const router = useRouter();
    const { playSound } = useSound();
    const { getActiveCoupons } = useCoupons();

    const [step, setStep] = useState(1);
    const [culqiLoading, setCulqiLoading] = useState(false);
    const [formData, setFormData] = useState({
        customer: '',
        phone: '',
        address: '',
        deliveryDate: '',
        deliveryTime: 'Mañana (9-1pm)',
        deliveryZone: 'Surco (Gratis)',
        paymentMethod: 'Yape / Plin',
        coupon: '',
        isGift: false,
        giftFrom: '',
        giftTo: '',
        giftMessage: '',
        notes: ''
    });

    const [appliedCoupon, setAppliedCoupon] = useState<any>(null);
    const [couponError, setCouponError] = useState('');
    const [phoneError, setPhoneError] = useState('');
    const [pointsInfo] = useState(() => {
        if (typeof window === 'undefined') return null;
        const info = getRedeemableDiscount();
        return info.points >= 100 ? info : null;
    });

    const deliveryPrices: Record<string, number> = {
        'Surco (Gratis)': 0,
        'San Borja (Gratis)': 0,
        'Miraflores (S/ 5.00)': 5,
        'San Isidro (S/ 5.00)': 5,
        'La Molina (S/ 8.00)': 8,
        'Otros (Consultar)': 0
    };

    const deliveryCost = deliveryPrices[formData.deliveryZone] || 0;

    let finalTotal = total + deliveryCost;
    if (appliedCoupon) {
        if (appliedCoupon.type === 'percent') finalTotal *= (1 - appliedCoupon.discount / 100);
        else finalTotal -= appliedCoupon.discount;
    }
    // Also reduce by redeemed loyalty points
    if (appliedCoupon?.type === 'points') finalTotal -= appliedCoupon.discount;
    finalTotal = Math.max(0, finalTotal);

    const handleApplyCoupon = () => {
        const code = formData.coupon.trim().toUpperCase();
        const coupons = getActiveCoupons();
        const found = coupons.find(c => c.code === code);

        if (found) {
            setAppliedCoupon(found);
            setCouponError('');
            showToast(`¡Cupón ${code} aplicado con éxito! ✨`, 'success');
        } else {
            setAppliedCoupon(null);
            setCouponError('Cupón inválido ❌');
            showToast('Cupón inválido o expirado ❌', 'error');
        }
    };

    const validateStep1 = () => {
        if (!formData.customer.trim()) {
            showToast('Por favor, ingresa tu nombre', 'error');
            return false;
        }
        if (!validatePeruvianPhone(formData.phone)) {
            showToast('Número de teléfono inválido', 'error');
            return false;
        }
        if (!formData.address.trim()) {
            showToast('La dirección es obligatoria', 'error');
            return false;
        }
        if (!formData.deliveryDate) {
            showToast('Selecciona una fecha de entrega', 'error');
            return false;
        }
        return true;
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();

        // Final Sanitization
        const sanitizedData = {
            ...formData,
            customer: sanitizeInput(formData.customer),
            address: sanitizeInput(formData.address),
            giftFrom: sanitizeInput(formData.giftFrom),
            giftTo: sanitizeInput(formData.giftTo),
            giftMessage: sanitizeInput(formData.giftMessage),
            notes: sanitizeInput(formData.notes)
        };

        const now = new Date();
        const yyyy = now.getFullYear();
        const mm = String(now.getMonth() + 1).padStart(2, '0');
        const dd = String(now.getDate()).padStart(2, '0');
        const rand = Math.random().toString(36).substr(2, 4).toUpperCase();
        const orderNum = `DM-${yyyy}${mm}${dd}-${rand}`;

        // 3. Save order via Firestore
        try {
            await createOrder({
                id: orderNum,
                date: now.toISOString(),
                customer: sanitizedData.customer,
                phone: sanitizedData.phone,
                address: sanitizedData.address,
                deliveryDate: sanitizedData.deliveryDate,
                deliveryTime: sanitizedData.deliveryTime,
                deliveryZone: sanitizedData.deliveryZone,
                paymentMethod: sanitizedData.paymentMethod,
                items: cart.map(i => ({ ...i })),
                total: finalTotal,
                subtotal: total,
                deliveryCost: deliveryCost,
                notes: sanitizedData.notes,
                isGift: sanitizedData.isGift,
                giftFrom: sanitizedData.giftFrom,
                giftTo: sanitizedData.giftTo,
                giftMessage: sanitizedData.giftMessage,
                couponUsed: appliedCoupon?.code || undefined,
                couponDiscount: appliedCoupon?.discount || undefined,
                customerPhone: sanitizedData.phone,
            });

            // Loyalty Points
            const pointsToAward = earnPoints(finalTotal);

            // WhatsApp notification
            const itemsDetail = cart.map(i => `  • ${i.quantity}x ${i.title} (${i.price})`).join('%0A');
            const message =
                (sanitizedData.isGift ? `🎁 *PEDIDO PARA REGALO* 🎁%0A` : '') +
                `🧾 *PEDIDO ${orderNum}*%0A` +
                `━━━━━━━━━━━━━━━━━━%0A` +
                `👤 *Cliente (Pago):* ${sanitizedData.customer}%0A` +
                `📞 *Tel:* ${sanitizedData.phone}%0A` +
                `📍 *Distrito:* ${sanitizedData.deliveryZone}%0A` +
                `🏠 *Dirección:* ${sanitizedData.address}%0A` +
                `📅 *Entrega:* ${sanitizedData.deliveryDate} - ${sanitizedData.deliveryTime}%0A` +
                (sanitizedData.isGift ? `━━━━━━━━━━━━━━━━━━%0A💌 *Para:* ${sanitizedData.giftTo}%0A👤 *De:* ${sanitizedData.giftFrom}%0A📝 *Dedicatoria:* "${sanitizedData.giftMessage}"%0A⚠️ *NOTA:* No enviar recibo al recibir.%0A` : '') +
                `💳 *Método de Pago:* ${sanitizedData.paymentMethod}%0A` +
                `━━━━━━━━━━━━━━━━━━%0A` +
                `🛒 *Detalle del Pedido:*%0A${itemsDetail}%0A` +
                (sanitizedData.notes ? `%0A📝 *Notas:* ${sanitizedData.notes.replace(/\n/g, '%0A')}` : '') +
                (appliedCoupon ? `%0A🏷️ *Cupón:* ${appliedCoupon.code} (-${appliedCoupon.type === 'percent' ? appliedCoupon.discount + '%' : 'S/ ' + appliedCoupon.discount})%0A` : '') +
                `━━━━━━━━━━━━━━━━━━%0A` +
                `💰 *TOTAL FINAL:* S/ ${finalTotal.toFixed(2)}%0A` +
                `━━━━━━━━━━━━━━━━━━%0A` +
                `Enviado desde antojitos-express.netlify.app 🍍`;

            const waNumber = content.whatsappNumber;
            const link = generateWhatsAppLink(waNumber, 'order', {
                orderId: orderNum,
                total: `S/ ${finalTotal.toFixed(2)}`,
                customerName: sanitizedData.customer
            }).replace(/text=.*/, `text=${encodeURIComponent(message)}`);

            window.open(link, '_blank');
            playSound('chime');
            clearCart();
            router.push(`/checkout/confirm?id=${orderNum}`);
        } catch (error) {
            console.error('Error submitting order:', error);
            showToast('Hubo un error al procesar tu pedido. Por favor, intenta de nuevo.', 'error');
        }
    };

    if (cart.length === 0) {
        return (
            <div className="container mx-auto px-4 py-20 text-center animate-fade-in">
                <div className="text-6xl mb-6">🛒</div>
                <h1 className="text-3xl font-fredoka font-bold text-primary mb-4">Tu carrito está vacío</h1>
                <p className="text-gray-500 mb-8">¡Aún no has añadido ningún antojo!</p>
                <button
                    onClick={() => router.push('/menu')}
                    className="bg-primary text-white px-8 py-3 rounded-full font-bold hover:bg-secondary transition-all shadow-lg"
                >
                    Explorar la Carta
                </button>
            </div>
        );
    }

    const steps = [
        { n: 1, name: 'Envío', icon: '🛵' },
        { n: 2, name: 'Regalo & Pago', icon: '🎁' },
        { n: 3, name: 'Revisión', icon: '✨' }
    ];

    return (
        <div className="container mx-auto px-4 py-12 max-w-5xl">
            {/* Progress Indicator */}
            <div className="mb-12 max-w-2xl mx-auto">
                <div className="flex justify-between relative">
                    <div className="absolute top-1/2 left-0 w-full h-0.5 bg-gray-100 -translate-y-1/2 -z-10" />
                    <div
                        className="absolute top-1/2 left-0 h-0.5 bg-secondary -translate-y-1/2 -z-10 transition-all duration-500"
                        style={{ width: `${((step - 1) / (steps.length - 1)) * 100}%` }}
                    />
                    {steps.map((s) => (
                        <div key={s.n} className="flex flex-col items-center gap-2 bg-paper px-2 text-center">
                            <div className={`w-10 h-10 rounded-full flex items-center justify-center font-bold transition-all shadow-sm ${step >= s.n ? 'bg-secondary text-white scale-110' : 'bg-white text-gray-300 border border-gray-100'
                                }`}>
                                {step > s.n ? '✓' : s.n}
                            </div>
                            <span className={`text-[10px] font-bold uppercase tracking-wider ${step >= s.n ? 'text-primary' : 'text-gray-300'}`}>
                                {s.icon} {s.name}
                            </span>
                        </div>
                    ))}
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-12 items-start">
                {/* Main Form Area */}
                <div className="lg:col-span-2 space-y-8 animate-fade-up">
                    <form onSubmit={handleSubmit} className="space-y-8">
                        {/* STEP 1: SHIPPING DETAILS */}
                        {step === 1 && (
                            <div className="bg-white p-8 rounded-[2rem] shadow-[0_20px_50px_rgba(0,0,0,0.05)] border border-primary/5 space-y-6 animate-reveal">
                                <h2 className="text-2xl font-fredoka font-bold text-primary flex items-center gap-3">
                                    <span className="w-8 h-8 bg-secondary/10 rounded-full flex items-center justify-center text-secondary text-sm">01</span>
                                    Datos de Entrega
                                </h2>

                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                    <div className="space-y-1">
                                        <label className="text-xs font-bold text-gray-400 uppercase ml-2">Nombre Completo</label>
                                        <input
                                            required
                                            value={formData.customer}
                                            placeholder="¿Quién recibe el antojo?"
                                            className="w-full p-4 bg-gray-50 border border-gray-100 rounded-2xl outline-none focus:border-secondary transition-all"
                                            onChange={e => setFormData({ ...formData, customer: e.target.value })}
                                        />
                                    </div>
                                    <div className="space-y-1">
                                        <label className="text-xs font-bold text-gray-400 uppercase ml-2">WhatsApp / Teléfono</label>
                                        <input
                                            required
                                            value={formData.phone}
                                            placeholder="987 654 321"
                                            type="tel"
                                            className={`w-full p-4 bg-gray-50 border rounded-2xl outline-none focus:border-secondary transition-all ${phoneError ? 'border-red-300' : 'border-gray-100'}`}
                                            onChange={e => {
                                                const val = e.target.value;
                                                setFormData({ ...formData, phone: val });
                                                if (val.length > 4) {
                                                    setPhoneError(validatePeruvianPhone(val) ? '' : 'Número peruano inválido (9 dígitos, empieza en 9)');
                                                } else {
                                                    setPhoneError('');
                                                }
                                            }}
                                        />
                                        {phoneError && <p className="text-xs text-red-500 ml-2 mt-1">{phoneError}</p>}
                                    </div>
                                </div>

                                <div className="space-y-4">
                                    <div>
                                        <label className="block text-sm font-bold text-gray-700 mb-2">Dirección de Entrega</label>
                                        <div className="relative">
                                            <input
                                                type="text"
                                                required
                                                className="w-full p-4 pl-12 bg-gray-50 border border-gray-100 rounded-2xl outline-none focus:border-secondary transition-all"
                                                value={formData.address}
                                                onChange={(e) => setFormData({ ...formData, address: e.target.value })}
                                                placeholder="Av. de las Artes Sur 123..."
                                            />
                                            <span className="absolute left-4 top-1/2 -translate-y-1/2 text-xl">📍</span>
                                            <button
                                                type="button"
                                                title="Usar mi ubicación actual"
                                                onClick={() => {
                                                    if ('geolocation' in navigator) {
                                                        showToast('📍 Buscando tu ubicación...', 'success');
                                                        navigator.geolocation.getCurrentPosition(
                                                            async (position) => {
                                                                try {
                                                                    const res = await fetch(`https://nominatim.openstreetmap.org/reverse?format=json&lat=${position.coords.latitude}&lon=${position.coords.longitude}`);
                                                                    const data = await res.json();
                                                                    if (data && data.display_name) {
                                                                        setFormData({ ...formData, address: data.display_name.split(',').slice(0, 3).join(', ') });
                                                                        showToast('✅ Ubicación encontrada', 'success');
                                                                    } else {
                                                                        showToast('❌ No se pudo resolver la dirección', 'error');
                                                                    }
                                                                } catch (e) {
                                                                    showToast('❌ Error de red al buscar dirección', 'error');
                                                                }
                                                            },
                                                            (error) => {
                                                                showToast('❌ Activa el GPS para usar esta función', 'error');
                                                            },
                                                            { timeout: 10000 }
                                                        );
                                                    } else {
                                                        showToast('❌ Tu navegador no soporta geolocalización', 'error');
                                                    }
                                                }}
                                                className="absolute right-4 top-1/2 -translate-y-1/2 text-2xl hover:scale-110 transition-transform bg-white rounded-full p-1 shadow-sm border border-gray-100"
                                            >
                                                🧭
                                            </button>
                                        </div>
                                        <p className="text-xs text-gray-400 mt-2 flex items-center gap-1">
                                            <span>💡</span> Toca la brújula para autocompletar con tu GPS.
                                        </p>
                                    </div>
                                </div>
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                    <div className="space-y-1">
                                        <label className="text-xs font-bold text-gray-400 uppercase ml-2">Distrito</label>
                                        <select
                                            className="w-full p-4 bg-gray-50 border border-gray-100 rounded-2xl outline-none focus:border-secondary appearance-none cursor-pointer"
                                            value={formData.deliveryZone}
                                            onChange={e => setFormData({ ...formData, deliveryZone: e.target.value })}
                                        >
                                            {Object.keys(deliveryPrices).map(zone => (
                                                <option key={zone} value={zone}>{zone}</option>
                                            ))}
                                        </select>
                                    </div>
                                    <div className="space-y-1">
                                        <label className="text-xs font-bold text-gray-400 uppercase ml-2">Fecha de Entrega</label>
                                        <input
                                            type="date"
                                            required
                                            value={formData.deliveryDate}
                                            min={new Date(Date.now() + 86400000).toISOString().split('T')[0]}
                                            className="w-full p-4 bg-gray-50 border border-gray-100 rounded-2xl outline-none focus:border-secondary"
                                            onChange={e => {
                                                const dateStr = e.target.value;
                                                if (!dateStr) {
                                                    setFormData({ ...formData, deliveryDate: '' });
                                                    return;
                                                }
                                                const date = new Date(dateStr);

                                                if (date.getUTCDay() === 0) {
                                                    showToast("Cerramos los domingos por descanso 🍍", "error");
                                                    e.target.value = "";
                                                    setFormData({ ...formData, deliveryDate: '' });
                                                    return;
                                                }

                                                if (layout.blockedDates && layout.blockedDates.includes(dateStr)) {
                                                    showToast("⚠️ Tenemos capacidad llena para esa fecha. ¡Por favor elige otra!", "error");
                                                    e.target.value = "";
                                                    setFormData({ ...formData, deliveryDate: '' });
                                                    return;
                                                }

                                                setFormData({ ...formData, deliveryDate: dateStr });
                                            }}
                                        />
                                    </div>
                                </div>

                                <div className="space-y-1">
                                    <label className="text-xs font-bold text-gray-400 uppercase ml-2">Rango Horario</label>
                                    <div className="grid grid-cols-3 gap-2">
                                        {['Mañana (9-1pm)', 'Tarde (2-6pm)', 'Noche (7-8pm)'].map(time => (
                                            <button
                                                key={time}
                                                type="button"
                                                onClick={() => setFormData({ ...formData, deliveryTime: time })}
                                                className={`p-3 rounded-xl text-[10px] md:text-xs font-bold transition-all border ${formData.deliveryTime === time
                                                    ? 'bg-primary text-white border-primary shadow-md'
                                                    : 'bg-white text-gray-400 border-gray-100 hover:border-primary/20'
                                                    }`}
                                            >
                                                {time.split(' ')[0]}
                                            </button>
                                        ))}
                                    </div>
                                </div>

                                <button
                                    type="button"
                                    onClick={() => validateStep1() && setStep(2)}
                                    className="w-full bg-secondary text-white py-4 rounded-2xl font-bold text-lg hover:brightness-110 transition-all shadow-xl shadow-secondary/20"
                                >
                                    Siguiente: Regalo & Pago →
                                </button>
                            </div>
                        )}

                        {/* STEP 2: GIFT & PAYMENT */}
                        {step === 2 && (
                            <div className="space-y-6 animate-reveal">
                                {/* Gift Options */}
                                <div className="bg-white p-8 rounded-[2rem] shadow-sm border border-primary/5 space-y-6">
                                    <div className="flex justify-between items-center">
                                        <h2 className="text-2xl font-fredoka font-bold text-primary flex items-center gap-3">
                                            <span className="w-8 h-8 bg-secondary/10 rounded-full flex items-center justify-center text-secondary text-sm">02</span>
                                            Detalles del Regalo
                                        </h2>
                                        <label className="relative inline-flex items-center cursor-pointer">
                                            <input type="checkbox" checked={formData.isGift} onChange={e => setFormData({ ...formData, isGift: e.target.checked })} className="sr-only peer" />
                                            <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-secondary"></div>
                                        </label>
                                    </div>

                                    {formData.isGift && (
                                        <div className="space-y-4 animate-reveal">
                                            <div className="grid grid-cols-2 gap-4">
                                                <input
                                                    placeholder="¿De parte de quién?"
                                                    className="w-full p-4 bg-gray-50 border border-gray-100 rounded-2xl outline-none"
                                                    value={formData.giftFrom}
                                                    onChange={e => setFormData({ ...formData, giftFrom: e.target.value })}
                                                />
                                                <input
                                                    placeholder="¿Para quién?"
                                                    className="w-full p-4 bg-gray-50 border border-gray-100 rounded-2xl outline-none"
                                                    value={formData.giftTo}
                                                    onChange={e => setFormData({ ...formData, giftTo: e.target.value })}
                                                />
                                            </div>
                                            <textarea
                                                rows={3}
                                                placeholder="Dedicatoria personalizada (se escribirá a mano) ✨"
                                                className="w-full p-4 bg-gray-50 border border-gray-100 rounded-2xl outline-none resize-none"
                                                value={formData.giftMessage}
                                                onChange={e => setFormData({ ...formData, giftMessage: e.target.value })}
                                            />
                                        </div>
                                    )}
                                </div>

                                {/* Payment Methods */}
                                <div className="bg-white p-8 rounded-[2rem] shadow-sm border border-primary/5 space-y-6">
                                    <h2 className="text-2xl font-fredoka font-bold text-primary">Método de Pago</h2>
                                    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                                        {[
                                            { id: 'Yape / Plin', icon: '📱' },
                                            { id: 'Tarjeta', icon: '💳' },
                                            { id: 'Transferencia', icon: '🏦' },
                                            { id: 'Efectivo', icon: '💵' }
                                        ].map(m => (
                                            <button
                                                key={m.id}
                                                type="button"
                                                onClick={() => setFormData({ ...formData, paymentMethod: m.id })}
                                                className={`p-4 rounded-2xl flex flex-col items-center gap-2 transition-all border ${formData.paymentMethod === m.id
                                                    ? 'bg-primary text-white border-primary shadow-lg scale-105'
                                                    : 'bg-paper text-primary border-transparent hover:border-primary/20'
                                                    }`}
                                            >
                                                <span className="text-xl">{m.icon}</span>
                                                <span className="text-[10px] font-bold uppercase">{m.id}</span>
                                            </button>
                                        ))}
                                    </div>
                                    <p className="text-[10px] text-gray-400 text-center italic mt-4 italic">
                                        * La coordinación final y confirmación de pago se realiza vía WhatsApp tras el pedido.
                                    </p>

                                    {/* Culqi Card Payment Button */}
                                    {formData.paymentMethod === 'Tarjeta' && isCulqiConfigured() && (
                                        <div className="mt-4 p-4 bg-blue-50 rounded-2xl border border-blue-100 text-center">
                                            <p className="text-xs text-blue-700 font-bold mb-3">💳 Paga ahora con tu tarjeta de crédito o débito</p>
                                            <button
                                                type="button"
                                                disabled={culqiLoading}
                                                onClick={async () => {
                                                    setCulqiLoading(true);
                                                    const token = await openCulqiModal({
                                                        amount: Math.round(finalTotal * 100),
                                                        customerEmail: `${formData.phone}@dulcesmoment0s.com`,
                                                        orderId: 'DM-PENDING',
                                                        description: `Pedido Antojitos Express`,
                                                    });
                                                    setCulqiLoading(false);
                                                    if (token) {
                                                        showToast('✅ Pago con tarjeta registrado. Confirmando pedido...', 'success');
                                                        setStep(3);
                                                    }
                                                }}
                                                className="bg-blue-600 text-white px-8 py-3 rounded-xl font-bold hover:bg-blue-700 transition-all disabled:opacity-60"
                                            >
                                                {culqiLoading ? 'Procesando...' : `Pagar S/ ${finalTotal.toFixed(2)} con Tarjeta`}
                                            </button>
                                            <p className="text-[10px] text-blue-500 mt-2">🔒 Seguro con Culqi — Visa, Mastercard y Amex</p>
                                        </div>
                                    )}
                                    {formData.paymentMethod === 'Tarjeta' && !isCulqiConfigured() && (
                                        <div className="mt-4 p-3 bg-yellow-50 rounded-xl border border-yellow-100">
                                            <p className="text-xs text-yellow-700 text-center">⚠️ Pago con tarjeta disponible próximamente. Por ahora elige Yape, Transferencia o Efectivo.</p>
                                        </div>
                                    )}
                                </div>

                                <div className="flex gap-4">
                                    <button onClick={() => setStep(1)} type="button" className="p-4 rounded-2xl border border-gray-200 text-gray-400 hover:text-primary transition-all">← Atrás</button>
                                    <button
                                        onClick={() => setStep(3)}
                                        type="button"
                                        className="flex-1 bg-secondary text-white py-4 rounded-2xl font-bold text-lg hover:brightness-110 transition-all shadow-xl"
                                    >Continuar al Resumen</button>
                                </div>
                            </div>
                        )}

                        {/* STEP 3: FINAL REVIEW */}
                        {step === 3 && (
                            <div className="bg-white p-8 rounded-[2rem] shadow-sm border border-primary/5 space-y-8 animate-reveal">
                                <h2 className="text-2xl font-fredoka font-bold text-primary flex items-center gap-3">
                                    <span className="w-8 h-8 bg-secondary/10 rounded-full flex items-center justify-center text-secondary text-sm">03</span>
                                    Última Revisión
                                </h2>

                                <div className="grid grid-cols-1 md:grid-cols-2 gap-8 text-sm">
                                    <div className="bg-paper/50 p-6 rounded-3xl space-y-3">
                                        <h3 className="font-bold text-secondary uppercase tracking-tighter text-xs">Resumen de Envío</h3>
                                        <p><strong>Recibe:</strong> {formData.customer}</p>
                                        <p><strong>Teléfono:</strong> {formData.phone}</p>
                                        <p><strong>Dirección:</strong> {formData.address}</p>
                                        <p><strong>Distrito:</strong> {formData.deliveryZone}</p>
                                        <p><strong>Fecha:</strong> {formData.deliveryDate} ({formData.deliveryTime})</p>
                                    </div>
                                    <div className="bg-paper/50 p-6 rounded-3xl space-y-3">
                                        <h3 className="font-bold text-secondary uppercase tracking-tighter text-xs">Otros Detalles</h3>
                                        <p><strong>Pago:</strong> {formData.paymentMethod}</p>
                                        <p><strong>Para regalo:</strong> {formData.isGift ? 'Sí 🎁' : 'No'}</p>
                                        {formData.notes && <p><strong>Notas:</strong> {formData.notes}</p>}
                                        <div className="pt-4 mt-2 border-t border-primary/10">
                                            {/* 🍬 Loyalty Points Banner */}
                                            {pointsInfo && !appliedCoupon && (
                                                <div className="mb-3 p-3 bg-amber-50 border border-amber-200 rounded-xl flex items-center justify-between gap-3 animate-fade-up">
                                                    <div>
                                                        <p className="text-xs font-bold text-amber-700">🍬 ¡Tienes {pointsInfo.points} puntos!</p>
                                                        <p className="text-[10px] text-amber-600">Puedes canjear S/ {pointsInfo.discount.toFixed(2)} de descuento.</p>
                                                    </div>
                                                    <button
                                                        type="button"
                                                        onClick={() => {
                                                            const result = redeemPoints(pointsInfo.points);
                                                            if (result) {
                                                                setAppliedCoupon({ code: 'PUNTOS', type: 'points', discount: result.discount });
                                                                showToast(`🍬 ¡${pointsInfo.points} puntos canjeados! -S/ ${result.discount.toFixed(2)}`, 'success');
                                                            }
                                                        }}
                                                        className="bg-amber-500 text-white text-xs font-bold px-3 py-2 rounded-lg hover:bg-amber-600 transition-all shrink-0"
                                                    >
                                                        Canjear
                                                    </button>
                                                </div>
                                            )}
                                            <div className="flex gap-2">
                                                <input
                                                    placeholder="Código de cupón"
                                                    className="flex-1 p-3 bg-white border border-gray-100 rounded-xl outline-none text-xs"
                                                    value={formData.coupon}
                                                    onChange={e => setFormData({ ...formData, coupon: e.target.value })}
                                                />
                                                <button onClick={handleApplyCoupon} type="button" className="bg-primary text-white px-4 rounded-xl text-xs font-bold hover:bg-secondary transition-colors">Aplicar</button>
                                            </div>
                                            {appliedCoupon && <p className="text-xs text-green-600 mt-2 font-bold">✓ {appliedCoupon.code === 'PUNTOS' ? 'Puntos canjeados' : 'Cupón activo'}!</p>}
                                        </div>
                                    </div>
                                </div>

                                <div className="flex gap-4">
                                    <button onClick={() => setStep(2)} type="button" className="p-4 rounded-2xl border border-gray-200 text-gray-400 hover:text-primary transition-all">← Atrás</button>
                                    <button
                                        type="submit"
                                        className="flex-1 bg-accent text-white py-5 rounded-3xl font-bold text-xl hover:scale-[1.02] active:scale-[0.98] transition-all shadow-2xl shadow-accent/20"
                                    >
                                        CONFIRMAR PEDIDO FINAL (S/ {finalTotal.toFixed(2)})
                                    </button>
                                </div>
                            </div>
                        )}
                    </form>
                </div>

                {/* Sticky Order Summary Sidebar */}
                <div className="lg:col-span-1 space-y-6 lg:sticky lg:top-24">
                    <div className="bg-primary text-paper p-8 rounded-[2rem] shadow-2xl overflow-hidden relative">
                        <div className="absolute top-0 right-0 w-32 h-32 bg-secondary/10 rounded-full -translate-y-1/2 translate-x-1/2 blur-3xl opacity-50" />

                        <h2 className="text-2xl font-fredoka font-bold mb-6 flex items-center justify-between border-b border-white/10 pb-4">
                            Regálate un Antojo 😋
                            <span className="text-xs font-nunito opacity-50 font-light">{cart.reduce((a, b) => a + b.quantity, 0)} items</span>
                        </h2>

                        <div className="space-y-4 mb-8 max-h-[300px] overflow-y-auto pr-2 custom-scrollbar">
                            {cart.map(item => (
                                <div key={item.id} className="flex justify-between items-start text-sm group">
                                    <div className="flex flex-col">
                                        <span className="font-medium group-hover:text-secondary transition-colors">{item.title}</span>
                                        <span className="text-[10px] opacity-60">Cantidad: {item.quantity}</span>
                                    </div>
                                    <span className="font-bold">S/ {(item.price * item.quantity).toFixed(2)}</span>
                                </div>
                            ))}
                        </div>

                        <div className="space-y-3 pt-6 border-t border-white/10 text-sm">
                            <div className="flex justify-between opacity-70">
                                <span>Subtotal</span>
                                <span>S/ {total.toFixed(2)}</span>
                            </div>
                            <div className="flex justify-between text-green-400">
                                <span>Delivery {formData.deliveryZone && `(${formData.deliveryZone.split(' ')[0]})`}</span>
                                <span>{deliveryCost > 0 ? `+ S/ ${deliveryCost.toFixed(2)}` : 'Gratis'}</span>
                            </div>
                            {appliedCoupon && (
                                <div className="flex justify-between text-secondary font-bold animate-reveal">
                                    <span>Cupón ({appliedCoupon.code})</span>
                                    <span>-{appliedCoupon.type === 'percent' ? `${appliedCoupon.discount}%` : `S/ ${appliedCoupon.discount}`}</span>
                                </div>
                            )}

                            <div className="flex justify-between items-center text-2xl font-bold pt-6 mt-4 border-t border-white/20">
                                <span>Total</span>
                                <span className="text-secondary tracking-tighter shadow-sm">S/ {finalTotal.toFixed(2)}</span>
                            </div>
                        </div>
                    </div>

                    {/* Trust Pillar */}
                    <div className="bg-white p-6 rounded-3xl border border-gray-100 flex items-center gap-4">
                        <div className="w-12 h-12 bg-green-50 rounded-full flex items-center justify-center text-green-500 text-xl">🛡️</div>
                        <div>
                            <p className="text-xs font-bold text-primary">Compra 100% Segura</p>
                            <p className="text-[10px] text-gray-400">Confirmación y coordinación inmediata por WhatsApp</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
