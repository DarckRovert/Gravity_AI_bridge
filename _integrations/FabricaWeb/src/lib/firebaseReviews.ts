/**
 * ⭐ Firebase Reviews Module — Dulces Momentos
 *
 * Handles customer reviews stored in Firestore.
 * Reviews are optionally verified against an orderId.
 */

import {
    collection,
    addDoc,
    getDocs,
    query,
    orderBy,
    Timestamp,
    where,
    limit,
} from 'firebase/firestore';
import { firestore, isFirebaseConfigured } from './firebase';

// ── Types ───────────────────────────────────────────────────────────────────

export interface Review {
    id?: string;
    orderId?: string;   // Optional order reference for verification
    product?: string;  // Product name (optional)
    rating: number;    // 1-5
    comment: string;
    customerName: string;
    verified: boolean; // true if orderId was validated
    createdAt: string;
}

// ── Local Fallback Store ─────────────────────────────────────────────────────

const LOCAL_REVIEWS_KEY = 'dm_reviews';

function getLocalReviews(): Review[] {
    try {
        const raw = localStorage.getItem(LOCAL_REVIEWS_KEY);
        return raw ? JSON.parse(raw) : [];
    } catch {
        return [];
    }
}

function saveLocalReview(review: Review): void {
    try {
        const existing = getLocalReviews();
        localStorage.setItem(LOCAL_REVIEWS_KEY, JSON.stringify([...existing, review]));
    } catch {
        //
    }
}

// ── Firestore Helpers ────────────────────────────────────────────────────────

/**
 * Verify if an orderId exists in Firestore orders collection.
 */
async function verifyOrder(orderId: string): Promise<boolean> {
    if (!isFirebaseConfigured() || !orderId) return false;
    try {
        const q = query(
            collection(firestore, 'orders'),
            where('__name__', '==', orderId),
            limit(1)
        );
        const snap = await getDocs(q);
        return !snap.empty;
    } catch {
        return false;
    }
}

// ── Public API ───────────────────────────────────────────────────────────────

/**
 * Submit a customer review.
 * If orderId is provided, verifies it against Firestore for the "verified" badge.
 */
export async function submitReview(data: {
    rating: number;
    comment: string;
    customerName: string;
    orderId?: string;
    product?: string;
}): Promise<{ success: boolean; error?: string }> {
    if (data.rating < 1 || data.rating > 5) return { success: false, error: 'Calificación inválida.' };
    if (!data.comment || data.comment.trim().length < 5) return { success: false, error: 'El comentario debe tener al menos 5 caracteres.' };
    if (!data.customerName || data.customerName.trim().length < 2) return { success: false, error: 'Ingresa tu nombre.' };

    const verified = data.orderId ? await verifyOrder(data.orderId) : false;

    const review: Review = {
        orderId: data.orderId,
        product: data.product,
        rating: data.rating,
        comment: data.comment.trim(),
        customerName: data.customerName.trim(),
        verified,
        createdAt: new Date().toISOString(),
    };

    if (!isFirebaseConfigured()) {
        saveLocalReview(review);
        return { success: true };
    }

    try {
        await addDoc(collection(firestore, 'reviews'), {
            ...review,
            createdAt: Timestamp.now(),
        });
        return { success: true };
    } catch (err) {
        saveLocalReview(review);
        return { success: true }; // Fallback success via localStorage
    }
}

/**
 * Fetch all public reviews (most recent first).
 */
export async function getReviews(limitTo = 50): Promise<Review[]> {
    if (!isFirebaseConfigured()) {
        return getLocalReviews().slice(-limitTo).reverse();
    }

    try {
        const q = query(
            collection(firestore, 'reviews'),
            orderBy('createdAt', 'desc'),
            limit(limitTo)
        );
        const snap = await getDocs(q);
        return snap.docs.map(doc => ({
            id: doc.id,
            ...doc.data(),
            createdAt: doc.data().createdAt?.toDate?.()?.toISOString() ?? new Date().toISOString(),
        } as Review));
    } catch {
        return getLocalReviews().slice(-limitTo).reverse();
    }
}

/**
 * Calculate average rating from reviews.
 */
export function getAverageRating(reviews: Review[]): number {
    if (reviews.length === 0) return 0;
    const sum = reviews.reduce((acc, r) => acc + r.rating, 0);
    return Math.round((sum / reviews.length) * 10) / 10;
}
