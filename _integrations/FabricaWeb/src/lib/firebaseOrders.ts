"use client";

/**
 * 🔥 Firestore Orders Manager — Dulces Momentos
 * 
 * Handles CRUD operations for orders.
 * Falls back to localStorage when Firebase is not configured.
 */

import {
    collection, doc, addDoc, getDoc, getDocs, updateDoc,
    query, orderBy, limit, where, onSnapshot, Timestamp,
    Unsubscribe
} from 'firebase/firestore';
import { firestore, isFirebaseConfigured } from './firebase';
import { Order } from './adminBrain';

// ========================
// 📋 ORDER STATUS PIPELINE
// ========================

export type OrderStatus =
    | 'nuevo'        // Just placed
    | 'confirmado'   // Payment verified
    | 'preparando'   // Being made
    | 'enviado'      // Out for delivery
    | 'entregado'    // Delivered
    | 'cancelado';   // Cancelled

export const ORDER_STATUS_FLOW: { status: OrderStatus; label: string; icon: string; color: string }[] = [
    { status: 'nuevo', label: 'Nuevo', icon: '🆕', color: '#f59e0b' },
    { status: 'confirmado', label: 'Confirmado', icon: '✅', color: '#10b981' },
    { status: 'preparando', label: 'Preparando', icon: '👨‍🍳', color: '#6366f1' },
    { status: 'enviado', label: 'Enviado', icon: '🛵', color: '#3b82f6' },
    { status: 'entregado', label: 'Entregado', icon: '🎉', color: '#22c55e' },
    { status: 'cancelado', label: 'Cancelado', icon: '❌', color: '#ef4444' },
];

// ========================
// 📦 EXTENDED ORDER TYPE
// ========================

export interface FirestoreOrder extends Order {
    status: OrderStatus;
    createdAt: string;
    updatedAt: string;
    deliveryZone?: string;
    paymentMethod: string;
    paymentConfirmed: boolean;
    isGift?: boolean;
    giftFrom?: string;
    giftTo?: string;
    giftMessage?: string;
    couponUsed?: string;
    couponDiscount?: number;
    deliveryCost?: number;
    subtotal?: number;
    customerPhone?: string;
}

// ========================
// 🔧 CRUD OPERATIONS
// ========================

const ORDERS_COLLECTION = 'orders';

/**
 * Create a new order — saves to Firestore if configured, localStorage as fallback
 */
export async function createOrder(orderData: Omit<FirestoreOrder, 'status' | 'createdAt' | 'updatedAt' | 'paymentConfirmed'>): Promise<FirestoreOrder> {
    const now = new Date().toISOString();
    const fullOrder: FirestoreOrder = {
        ...orderData,
        status: 'nuevo',
        createdAt: now,
        updatedAt: now,
        paymentConfirmed: false,
    };

    if (isFirebaseConfigured()) {
        try {
            const docRef = await addDoc(collection(firestore, ORDERS_COLLECTION), fullOrder);
            fullOrder.id = docRef.id; // Use Firestore doc ID
            // Also update the document with its own ID for easier querying
            await updateDoc(docRef, { firestoreId: docRef.id });
        } catch (error) {
            console.error('🔥 Firestore write failed, falling back to localStorage:', error);
            saveOrderToLocalStorage(fullOrder);
        }
    } else {
        saveOrderToLocalStorage(fullOrder);
    }

    return fullOrder;
}

/**
 * Get all orders — from Firestore or localStorage
 */
export async function getOrders(limitCount: number = 100): Promise<FirestoreOrder[]> {
    if (isFirebaseConfigured()) {
        try {
            const q = query(
                collection(firestore, ORDERS_COLLECTION),
                orderBy('createdAt', 'desc'),
                limit(limitCount)
            );
            const snapshot = await getDocs(q);
            return snapshot.docs.map(doc => ({
                ...doc.data(),
                id: doc.data().id || doc.id,
            })) as FirestoreOrder[];
        } catch (error) {
            console.error('🔥 Firestore read failed, falling back to localStorage:', error);
            return getOrdersFromLocalStorage();
        }
    }
    return getOrdersFromLocalStorage();
}

/**
 * Get a single order by its ID
 */
export async function getOrderById(orderId: string): Promise<FirestoreOrder | null> {
    if (isFirebaseConfigured()) {
        try {
            // First try direct doc lookup
            const docSnap = await getDoc(doc(firestore, ORDERS_COLLECTION, orderId));
            if (docSnap.exists()) {
                return { ...docSnap.data(), id: docSnap.id } as FirestoreOrder;
            }
            // If not found by document ID, search by order ID field
            const q = query(
                collection(firestore, ORDERS_COLLECTION),
                where('id', '==', orderId),
                limit(1)
            );
            const snapshot = await getDocs(q);
            if (!snapshot.empty) {
                const d = snapshot.docs[0];
                return { ...d.data(), id: d.data().id || d.id } as FirestoreOrder;
            }
            return null;
        } catch (error) {
            console.error('🔥 Firestore lookup failed:', error);
            return getOrderFromLocalStorage(orderId);
        }
    }
    return getOrderFromLocalStorage(orderId);
}

/**
 * Update order status
 */
export async function updateOrderStatus(orderId: string, newStatus: OrderStatus): Promise<boolean> {
    const now = new Date().toISOString();

    if (isFirebaseConfigured()) {
        try {
            // Find the document by order ID
            const q = query(
                collection(firestore, ORDERS_COLLECTION),
                where('id', '==', orderId),
                limit(1)
            );
            const snapshot = await getDocs(q);
            if (!snapshot.empty) {
                await updateDoc(snapshot.docs[0].ref, {
                    status: newStatus,
                    updatedAt: now,
                    paymentConfirmed: newStatus !== 'nuevo' && newStatus !== 'cancelado',
                });
                return true;
            }
            return false;
        } catch (error) {
            console.error('🔥 Firestore update failed:', error);
            return updateOrderInLocalStorage(orderId, { status: newStatus, updatedAt: now });
        }
    }
    return updateOrderInLocalStorage(orderId, { status: newStatus, updatedAt: now });
}

/**
 * Confirm payment for an order
 */
export async function confirmPayment(orderId: string): Promise<boolean> {
    return updateOrderStatus(orderId, 'confirmado');
}

/**
 * Subscribe to real-time order updates (Firestore only)
 * Returns an unsubscribe function, or null if using localStorage
 */
export function subscribeToOrders(
    callback: (orders: FirestoreOrder[]) => void,
    limitCount: number = 50
): Unsubscribe | null {
    if (!isFirebaseConfigured()) {
        // For localStorage, just call once
        callback(getOrdersFromLocalStorage());
        return null;
    }

    try {
        const q = query(
            collection(firestore, ORDERS_COLLECTION),
            orderBy('createdAt', 'desc'),
            limit(limitCount)
        );

        return onSnapshot(q, (snapshot) => {
            const orders = snapshot.docs.map(doc => ({
                ...doc.data(),
                id: doc.data().id || doc.id,
            })) as FirestoreOrder[];
            callback(orders);
        }, (error) => {
            console.error('🔥 Firestore listener error:', error);
            callback(getOrdersFromLocalStorage());
        });
    } catch (error) {
        console.error('🔥 Firestore subscribe failed:', error);
        callback(getOrdersFromLocalStorage());
        return null;
    }
}

/**
 * Get orders by status
 */
export async function getOrdersByStatus(status: OrderStatus): Promise<FirestoreOrder[]> {
    if (isFirebaseConfigured()) {
        try {
            const q = query(
                collection(firestore, ORDERS_COLLECTION),
                where('status', '==', status),
                orderBy('createdAt', 'desc')
            );
            const snapshot = await getDocs(q);
            return snapshot.docs.map(doc => ({
                ...doc.data(),
                id: doc.data().id || doc.id,
            })) as FirestoreOrder[];
        } catch (error) {
            console.error('🔥 Firestore query failed:', error);
        }
    }
    return getOrdersFromLocalStorage().filter(o => o.status === status);
}

/**
 * Get today's orders count and revenue
 */
export async function getTodaySummary(): Promise<{ count: number; revenue: number }> {
    const orders = await getOrders(200);
    const today = new Date().toISOString().split('T')[0];
    const todayOrders = orders.filter(o =>
        o.createdAt.startsWith(today) && o.status !== 'cancelado'
    );
    return {
        count: todayOrders.length,
        revenue: todayOrders.reduce((sum, o) => sum + (o.total || 0), 0),
    };
}

// ========================
// 💾 LOCALSTORAGE FALLBACK
// ========================

function saveOrderToLocalStorage(order: FirestoreOrder): void {
    try {
        const existing = JSON.parse(localStorage.getItem('dm_orders') || '[]');
        existing.unshift(order);
        localStorage.setItem('dm_orders', JSON.stringify(existing));
    } catch (e) {
        console.error('localStorage write failed:', e);
    }
}

/**
 * Synchronous order read — for hooks/callbacks that can't use async.
 * Uses localStorage directly (Firestore is always async).
 */
export function getOrdersSync(): FirestoreOrder[] {
    return getOrdersFromLocalStorage();
}

function getOrdersFromLocalStorage(): FirestoreOrder[] {
    try {
        const orders = JSON.parse(localStorage.getItem('dm_orders') || '[]');
        // Ensure old orders have the new fields
        return orders.map((o: Record<string, unknown>) => ({
            ...o,
            status: o.status || 'nuevo',
            createdAt: o.createdAt || o.date || new Date().toISOString(),
            updatedAt: o.updatedAt || o.date || new Date().toISOString(),
            paymentConfirmed: o.paymentConfirmed ?? false,
            paymentMethod: o.paymentMethod || 'No especificado',
        })) as FirestoreOrder[];
    } catch (e) {
        console.error('localStorage read failed:', e);
        return [];
    }
}

function getOrderFromLocalStorage(orderId: string): FirestoreOrder | null {
    const orders = getOrdersFromLocalStorage();
    return orders.find(o => o.id === orderId) || null;
}

function updateOrderInLocalStorage(orderId: string, updates: Partial<FirestoreOrder>): boolean {
    try {
        const orders = getOrdersFromLocalStorage();
        const index = orders.findIndex(o => o.id === orderId);
        if (index === -1) return false;
        orders[index] = { ...orders[index], ...updates };
        localStorage.setItem('dm_orders', JSON.stringify(orders));
        return true;
    } catch (e) {
        console.error('localStorage update failed:', e);
        return false;
    }
}
