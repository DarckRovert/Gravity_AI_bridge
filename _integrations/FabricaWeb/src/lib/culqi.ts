/**
 * 💳 Culqi Integration — Dulces Momentos
 *
 * Culqi is the leading Peruvian payment gateway (https://culqi.com).
 * This module handles the Culqi.js SDK loading and charge creation.
 *
 * ⚠️  SETUP REQUIRED:
 *  1. Create a Culqi account at https://culqi.com and verify it.
 *  2. In the Culqi Dashboard → Developers → API Keys:
 *     - Copy your PUBLIC key → NEXT_PUBLIC_CULQI_PUBLIC_KEY in .env.local
 *     - Copy your SECRET key → CULQI_SECRET_KEY in .env.local (server-side only!)
 *  3. For production charges, you need a server-side API route that uses CULQI_SECRET_KEY.
 *     The charges endpoint is: POST https://api.culqi.com/v2/charges
 *     (see https://docs.culqi.com for full reference)
 *
 * This file handles:
 *  - Loading the Culqi.js SDK dynamically
 *  - Opening the Culqi payment popup (culqiSettings + Culqi.open())
 *  - Returning the generated token to the caller
 */

// ── Types ─────────────────────────────────────────────────────────────────────

export interface CulqiToken {
    object: 'token';
    id: string;
    email: string;
    card_number: string; // Last 4 digits shown as "XXXX XXXX XXXX 1234"
    brand: string;
}

export interface CulqiChargeRequest {
    amount: number;        // In centavos (e.g., 10000 = S/100.00)
    currency?: string;     // Default: 'PEN'
    description?: string;
    customerEmail: string;
    orderId: string;
}

export interface CulqiChargeResponse {
    success: boolean;
    chargeId?: string;
    error?: string;
}

// ── Helpers ───────────────────────────────────────────────────────────────────

declare global {
    interface Window {
        Culqi?: {
            publicKey: string;
            settings: (config: object) => void;
            open: () => void;
            close: () => void;
            token?: CulqiToken;
        };
        culqi?: () => void;
    }
}

const CULQI_SCRIPT_SRC = 'https://checkout.culqi.com/js/v4';
let culqiScriptPromise: Promise<void> | null = null;

/**
 * Load the Culqi.js SDK once, caching the promise.
 */
function loadCulqiSDK(): Promise<void> {
    if (culqiScriptPromise) return culqiScriptPromise;

    culqiScriptPromise = new Promise<void>((resolve, reject) => {
        if (typeof window === 'undefined') { resolve(); return; }
        if (window.Culqi) { resolve(); return; }

        const script = document.createElement('script');
        script.src = CULQI_SCRIPT_SRC;
        script.async = true;
        script.onload = () => resolve();
        script.onerror = () => reject(new Error('Failed to load Culqi SDK'));
        document.head.appendChild(script);
    });

    return culqiScriptPromise;
}

/**
 * Check if we have a Culqi public key configured.
 */
export function isCulqiConfigured(): boolean {
    return !!process.env.NEXT_PUBLIC_CULQI_PUBLIC_KEY;
}

/**
 * Open the Culqi payment modal.
 * Returns a CulqiToken when the user completes the card form,
 * or null if cancelled / SDK not available.
 *
 * @example
 * const token = await openCulqiModal({ amount: 15000, customerEmail: 'x@y.com', orderId: 'DM-001', description: 'Torta de Chocolate' });
 * if (token) { ... send token.id to your backend to create charge }
 */
export async function openCulqiModal(config: CulqiChargeRequest): Promise<CulqiToken | null> {
    if (!isCulqiConfigured()) {
        console.warn('[Culqi] Public key not configured. Set NEXT_PUBLIC_CULQI_PUBLIC_KEY in .env.local');
        return null;
    }

    try {
        await loadCulqiSDK();
    } catch {
        console.error('[Culqi] Failed to load SDK.');
        return null;
    }

    if (!window.Culqi) return null;

    // Capture in local variable so TypeScript narrows the type to non-undefined
    const culqiSDK = window.Culqi;

    const publicKey = process.env.NEXT_PUBLIC_CULQI_PUBLIC_KEY!;
    culqiSDK.publicKey = publicKey;
    culqiSDK.settings({
        title: 'Dulces Momentos',
        currency: config.currency ?? 'PEN',
        description: config.description ?? `Pedido ${config.orderId}`,
        amount: config.amount,
    });

    return new Promise<CulqiToken | null>((resolve) => {
        // Culqi calls window.culqi() with the token when payment completes
        window.culqi = () => {
            const token = window.Culqi?.token ?? null;
            window.Culqi?.close();
            resolve(token);
        };
        culqiSDK.open();

        // Listen for modal close without payment (escape / X button)
        const onKeydown = (e: KeyboardEvent) => {
            if (e.key === 'Escape') {
                resolve(null);
                document.removeEventListener('keydown', onKeydown);
            }
        };
        document.addEventListener('keydown', onKeydown);
    });
}

/**
 * Create a charge server-side via Next.js API route.
 * Requires /api/culqi-charge to exist (see recommendation below).
 *
 * The API route should:
 *  1. Receive { tokenId, amount, email, orderId }
 *  2. POST to https://api.culqi.com/v2/charges with Authorization: Bearer CULQI_SECRET_KEY
 *  3. Return { success, chargeId } or { success: false, error }
 */
export async function createCulqiCharge(
    tokenId: string,
    request: CulqiChargeRequest
): Promise<CulqiChargeResponse> {
    try {
        const res = await fetch('/api/culqi-charge', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                tokenId,
                amount: request.amount,
                email: request.customerEmail,
                orderId: request.orderId,
                description: request.description ?? `Pedido ${request.orderId}`,
            }),
        });

        if (!res.ok) {
            const err = await res.json();
            return { success: false, error: err.message ?? 'Error procesando el pago.' };
        }

        const data = await res.json();
        return { success: true, chargeId: data.id };
    } catch (err) {
        return { success: false, error: 'Error de conexión. Intenta de nuevo.' };
    }
}
