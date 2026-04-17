"use client";

/**
 * 🔔 PushNotificationBanner — Dulces Momentos
 *
 * Non-intrusive banner that appears after 30 seconds or after the user's
 * first order, inviting them to subscribe to push notifications.
 *
 * Renders nothing if:
 *  - The user already granted permission
 *  - FCM is not configured (no VAPID key / no Firebase)
 *  - The user previously dismissed the banner
 */

import { useState, useEffect } from 'react';
import { requestPushPermission, hasPushPermission } from '@/lib/fcm';

const DISMISSED_KEY = 'dm_push_dismissed';

export default function PushNotificationBanner() {
    const [visible, setVisible] = useState(false);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        // Don't show if already granted or dismissed before
        if (hasPushPermission()) return;
        if (typeof window !== 'undefined' && localStorage.getItem(DISMISSED_KEY)) return;

        // Appear after 30 seconds
        const timer = setTimeout(() => setVisible(true), 30_000);
        return () => clearTimeout(timer);
    }, []);

    const dismiss = () => {
        localStorage.setItem(DISMISSED_KEY, '1');
        setVisible(false);
    };

    const subscribe = async () => {
        setLoading(true);
        const token = await requestPushPermission();
        setLoading(false);
        if (token) {
            setVisible(false);
        }
    };

    if (!visible) return null;

    return (
        <div
            role="alert"
            className="fixed bottom-20 left-4 right-4 md:left-auto md:right-6 md:w-96 z-50 animate-fade-up"
        >
            <div className="bg-white rounded-2xl shadow-2xl border border-gray-100 p-5 flex gap-4 items-start">
                <div className="text-3xl select-none">🔔</div>
                <div className="flex-1">
                    <p className="font-bold text-gray-900 mb-1">¡Mantente al día!</p>
                    <p className="text-sm text-gray-500">
                        Activa las notificaciones para saber cuándo tu pedido sale a camino.
                    </p>
                    <div className="flex gap-2 mt-3">
                        <button
                            onClick={subscribe}
                            disabled={loading}
                            className="bg-primary text-white text-sm font-bold px-4 py-2 rounded-xl hover:bg-secondary transition-all disabled:opacity-60"
                        >
                            {loading ? 'Activando...' : 'Activar'}
                        </button>
                        <button
                            onClick={dismiss}
                            className="text-gray-400 text-sm font-medium px-4 py-2 rounded-xl hover:bg-gray-100 transition-all"
                        >
                            Ahora no
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}
