"use client";

import { useSearchParams, useRouter } from 'next/navigation';
import { useEffect, useState, Suspense } from 'react';
import { getOrderById, FirestoreOrder, ORDER_STATUS_FLOW } from '@/lib/firebaseOrders';

function ConfirmContent() {
    const searchParams = useSearchParams();
    const router = useRouter();
    const orderId = searchParams.get('id');
    const [order, setOrder] = useState<FirestoreOrder | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        async function fetchOrder() {
            if (orderId) {
                const found = await getOrderById(orderId);
                setOrder(found);
            }
            setLoading(false);
        }
        fetchOrder();
    }, [orderId]);

    if (loading) {
        return (
            <div className="container mx-auto px-4 py-20 text-center">
                <div className="animate-pulse">
                    <div className="text-4xl mb-4">🔍</div>
                    <p className="text-lg text-gray-500">Buscando tu pedido...</p>
                </div>
            </div>
        );
    }

    if (!order) {
        return (
            <div className="container mx-auto px-4 py-20 text-center">
                <div className="text-4xl mb-4">😕</div>
                <h1 className="text-2xl font-bold mb-4">Pedido no encontrado</h1>
                <p className="text-gray-500 mb-6">El código <strong>{orderId}</strong> no existe en nuestro sistema.</p>
                <button
                    onClick={() => router.push('/')}
                    className="bg-primary text-white px-6 py-3 rounded-xl hover:opacity-90 transition"
                >
                    Volver al inicio
                </button>
            </div>
        );
    }

    const currentStatusIndex = ORDER_STATUS_FLOW.findIndex(s => s.status === order.status);

    return (
        <div className="container mx-auto px-4 py-12 max-w-2xl">
            {/* Success Header */}
            <div className="text-center mb-8">
                <div className="text-6xl mb-4 animate-bounce">🎉</div>
                <h1 className="text-3xl font-playfair font-bold text-primary mb-2">
                    ¡Pedido Registrado!
                </h1>
                <p className="text-gray-500">Tu pedido ha sido recibido exitosamente</p>
            </div>

            {/* Order Code */}
            <div className="bg-gradient-to-r from-primary/10 to-secondary/10 rounded-2xl p-6 text-center mb-6 border border-primary/20">
                <p className="text-sm text-gray-500 mb-1">Código de pedido</p>
                <p className="text-3xl font-mono font-bold text-primary tracking-wider">{order.id}</p>
                <p className="text-xs text-gray-400 mt-2">Guarda este código para rastrear tu pedido</p>
            </div>

            {/* Status Pipeline */}
            <div className="bg-white rounded-2xl border border-gray-100 p-6 mb-6 shadow-sm">
                <h2 className="text-lg font-bold mb-4">📦 Estado del Pedido</h2>
                <div className="flex items-center justify-between">
                    {ORDER_STATUS_FLOW.filter(s => s.status !== 'cancelado').map((step, index) => (
                        <div key={step.status} className="flex flex-col items-center flex-1">
                            <div
                                className={`w-10 h-10 rounded-full flex items-center justify-center text-lg transition-all duration-300 ${index <= currentStatusIndex
                                    ? 'bg-primary/20 scale-110'
                                    : 'bg-gray-100 opacity-40'
                                    }`}
                            >
                                {step.icon}
                            </div>
                            <span className={`text-[10px] mt-1 text-center ${index <= currentStatusIndex ? 'text-primary font-bold' : 'text-gray-300'
                                }`}>
                                {step.label}
                            </span>
                            {index < ORDER_STATUS_FLOW.filter(s => s.status !== 'cancelado').length - 1 && (
                                <div className={`hidden sm:block absolute w-8 h-0.5 ${index < currentStatusIndex ? 'bg-primary' : 'bg-gray-200'
                                    }`} style={{ transform: 'translateX(100%)' }} />
                            )}
                        </div>
                    ))}
                </div>
            </div>

            {/* Order Details */}
            <div className="bg-white rounded-2xl border border-gray-100 p-6 mb-6 shadow-sm">
                <h2 className="text-lg font-bold mb-4">🧾 Detalle del Pedido</h2>
                <div className="space-y-2">
                    {order.items?.map((item, i) => (
                        <div key={i} className="flex justify-between text-sm">
                            <span>{item.quantity}x {item.title}</span>
                            <span className="text-gray-500">S/ {((item.price || 0) * item.quantity).toFixed(2)}</span>
                        </div>
                    ))}
                    <hr className="my-3" />
                    {order.couponUsed && (
                        <div className="flex justify-between text-sm text-green-600">
                            <span>🏷️ Cupón: {order.couponUsed}</span>
                            <span>-{order.couponDiscount}%</span>
                        </div>
                    )}
                    {(order.deliveryCost || 0) > 0 && (
                        <div className="flex justify-between text-sm">
                            <span>🛵 Delivery</span>
                            <span>S/ {order.deliveryCost?.toFixed(2)}</span>
                        </div>
                    )}
                    <div className="flex justify-between text-lg font-bold text-primary pt-2">
                        <span>Total</span>
                        <span>S/ {(order.total || 0).toFixed(2)}</span>
                    </div>
                </div>
            </div>

            {/* Payment Info */}
            <div className="bg-amber-50 rounded-2xl border border-amber-200 p-6 mb-6">
                <h2 className="text-lg font-bold mb-2">💳 Pago: {order.paymentMethod}</h2>
                {order.paymentMethod?.includes('Yape') || order.paymentMethod?.includes('Plin') ? (
                    <div className="space-y-4">
                        <p className="text-sm text-amber-700">
                            Escanea el QR o envía <strong>S/ {(order.total || 0).toFixed(2)}</strong> al Yape/Plin y adjunta la captura por WhatsApp.
                        </p>
                        <div className="flex justify-center">
                            {/* eslint-disable-next-line @next/next/no-img-element */}
                            <img
                                src="/img/yape.jpeg"
                                alt="QR de pago Yape - Rodrigo Alejandro Vega Rojas"
                                className="w-56 h-auto rounded-2xl shadow-md border border-amber-200"
                            />
                        </div>
                        <p className="text-center text-sm font-semibold text-primary">
                            Rodrigo Alejandro Vega Rojas
                        </p>
                        <p className="text-xs text-amber-600 text-center">
                            Tu pedido se confirmará una vez verificado el pago.
                        </p>
                    </div>
                ) : (
                    <p className="text-sm text-amber-700">
                        {order.paymentMethod === 'Efectivo'
                            ? 'Pago al momento de la entrega. Ten el monto exacto listo.'
                            : 'Te enviaremos los datos de transferencia por WhatsApp.'}
                    </p>
                )}
            </div>

            {/* Customer Info */}
            <div className="bg-white rounded-2xl border border-gray-100 p-6 mb-6 shadow-sm">
                <h2 className="text-lg font-bold mb-3">📍 Datos de Entrega</h2>
                <div className="grid grid-cols-2 gap-3 text-sm">
                    <div>
                        <span className="text-gray-400">Cliente</span>
                        <p className="font-medium">{order.customer}</p>
                    </div>
                    <div>
                        <span className="text-gray-400">Teléfono</span>
                        <p className="font-medium">{order.phone}</p>
                    </div>
                    <div>
                        <span className="text-gray-400">Dirección</span>
                        <p className="font-medium">{order.address}</p>
                    </div>
                    <div>
                        <span className="text-gray-400">Entrega</span>
                        <p className="font-medium">{order.deliveryDate} - {order.deliveryTime}</p>
                    </div>
                </div>
            </div>

            {order.isGift && (
                <div className="bg-pink-50 rounded-2xl border border-pink-200 p-6 mb-6">
                    <h2 className="text-lg font-bold mb-2">🎁 Pedido de Regalo</h2>
                    <p className="text-sm"><strong>Para:</strong> {order.giftTo}</p>
                    <p className="text-sm"><strong>De:</strong> {order.giftFrom}</p>
                    {order.giftMessage && <p className="text-sm italic mt-2">&quot;{order.giftMessage}&quot;</p>}
                </div>
            )}

            {/* Actions */}
            <div className="flex flex-col gap-3">
                <button
                    onClick={() => router.push(`/tracker?code=${order.id}`)}
                    className="w-full bg-primary text-white py-3 rounded-xl font-bold text-lg hover:opacity-90 transition shadow-lg"
                >
                    📦 Rastrear Pedido
                </button>
                <button
                    onClick={() => router.push('/menu')}
                    className="w-full bg-white text-primary py-3 rounded-xl font-bold text-lg border-2 border-primary/20 hover:bg-primary/5 transition"
                >
                    🛒 Seguir Comprando
                </button>
            </div>
        </div>
    );
}

export default function ConfirmPage() {
    return (
        <Suspense fallback={
            <div className="container mx-auto px-4 py-20 text-center">
                <div className="animate-pulse text-4xl">🔍</div>
            </div>
        }>
            <ConfirmContent />
        </Suspense>
    );
}
