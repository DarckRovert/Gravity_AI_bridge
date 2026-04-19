/**
 * 🔔 Firebase Cloud Messaging (FCM) — Dulces Momentos
 *
 * Sends push notifications to the admin when a new order arrives,
 * and to the customer when their order status changes.
 *
 * ⚠️  SETUP REQUIRED:
 *  1. In Firebase Console → Project Settings → Cloud Messaging → Web Push Certificates
 *     Generate a VAPID key pair and add it to your .env.local:
 *     NEXT_PUBLIC_FIREBASE_VAPID_KEY=<your-vapid-key>
 *  2. Firebase will send push notifications to subscribers.
 *     The server-side Admin SDK is needed to push from the backend;
 *     here we handle the browser subscription side.
 */

import { getMessaging, getToken, onMessage, Messaging } from 'firebase/messaging';
import { firebaseApp, isFirebaseConfigured } from './firebase';

// ── Types ─────────────────────────────────────────────────────────────────────

export interface PushSubscription {
    token: string;
    topic: 'admin' | 'customer';
    orderId?: string;
}

// ── Local Storage Keys ─────────────────────────────────────────────────────────

const FCM_TOKEN_KEY = 'dm_fcm_token';
const FCM_PERMISSION_KEY = 'dm_fcm_permission';

// ── Helpers ───────────────────────────────────────────────────────────────────

function getVapidKey(): string | null {
    return process.env.NEXT_PUBLIC_FIREBASE_VAPID_KEY ?? null;
}

function isFCMSupported(): boolean {
    return (
        typeof window !== 'undefined' &&
        'Notification' in window &&
        'serviceWorker' in navigator &&
        isFirebaseConfigured() &&
        !!getVapidKey()
    );
}

// ── Public API ────────────────────────────────────────────────────────────────

/**
 * Request push notification permission and get the FCM token.
 * Stores the token in localStorage for later use.
 * Returns the token string, or null if permission was denied / FCM not available.
 */
export async function requestPushPermission(): Promise<string | null> {
    if (!isFCMSupported()) {
        console.info('[FCM] Not supported in this environment.');
        return null;
    }

    try {
        const permission = await Notification.requestPermission();
        localStorage.setItem(FCM_PERMISSION_KEY, permission);

        if (permission !== 'granted') {
            console.info('[FCM] Permission denied.');
            return null;
        }

        const messaging: Messaging = getMessaging(firebaseApp);
        const token = await getToken(messaging, { vapidKey: getVapidKey()! });

        if (token) {
            localStorage.setItem(FCM_TOKEN_KEY, token);
            console.info('[FCM] Token obtained:', token.slice(0, 20) + '...');
            return token;
        }

        return null;
    } catch (err) {
        console.warn('[FCM] Error getting token:', err);
        return null;
    }
}

/**
 * Get the previously stored FCM token (if any).
 */
export function getStoredToken(): string | null {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem(FCM_TOKEN_KEY);
}

/**
 * Check if the user has already granted push notifications permission.
 */
export function hasPushPermission(): boolean {
    if (typeof window === 'undefined') return false;
    return Notification.permission === 'granted';
}

/**
 * Listen for incoming FCM messages while the app is in the foreground.
 * Returns an unsubscribe function.
 */
export function onForegroundMessage(
    callback: (payload: { title?: string; body?: string; icon?: string }) => void
): (() => void) | null {
    if (!isFCMSupported()) return null;

    try {
        const messaging: Messaging = getMessaging(firebaseApp);
        return onMessage(messaging, (payload) => {
            callback({
                title: payload.notification?.title,
                body: payload.notification?.body,
                icon: payload.notification?.icon,
            });
        });
    } catch (err) {
        console.warn('[FCM] Could not set up message listener:', err);
        return null;
    }
}

/**
 * Show a browser-native notification in the foreground
 * (used as fallback when FCM message arrives while app is open).
 */
export function showLocalNotification(title: string, body: string, icon = '/img/icon-192.png'): void {
    if (typeof window === 'undefined' || !('Notification' in window)) return;
    if (Notification.permission !== 'granted') return;

    try {
        new Notification(title, { body, icon });
    } catch {
        // Some browsers require ServiceWorker notifications — silently skip
    }
}
