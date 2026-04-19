// ========================
// 🔐 Auth Module — Dulces Momentos
// ========================

/**
 * Hash a password using SHA-256 via Web Crypto API
 */
export async function hashPassword(password: string): Promise<string> {
    const encoder = new TextEncoder();
    const data = encoder.encode(password);
    const hashBuffer = await crypto.subtle.digest('SHA-256', data);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
}

/**
 * Generate a cryptographic session token.
 * Combines a random UUID with a timestamp for validation.
 */
export function generateSessionToken(): string {
    const token = crypto.randomUUID();
    const timestamp = Date.now().toString(36);
    return `${token}-${timestamp}`;
}

/**
 * Validate that a session token has the correct format and is not expired.
 * @param token The session token to validate
 * @param maxAgeMs Maximum age in milliseconds (default: 8 hours)
 */
export function isValidSessionToken(token: string | null, maxAgeMs: number = 8 * 60 * 60 * 1000): boolean {
    if (!token) return false;

    // Token format: uuid-timestamp(base36)
    const parts = token.split('-');
    if (parts.length < 6) return false; // UUID has 5 parts + timestamp

    const timestampPart = parts[parts.length - 1];
    const createdAt = parseInt(timestampPart, 36);

    if (isNaN(createdAt)) return false;
    if (Date.now() - createdAt > maxAgeMs) return false;

    return true;
}

// In-memory rate limit store (not clearable via DevTools)
const rateLimitStore = new Map<string, { count: number; firstRequest: number }>();

/**
 * Rate limiting with in-memory primary store.
 * Falls back to localStorage for persistence across page reloads,
 * but the in-memory store prevents console-based bypass.
 */
export function checkRateLimit(key: string, limit: number, windowMs: number): boolean {
    const now = Date.now();

    // Check in-memory store first (tamper-resistant)
    const memRecord = rateLimitStore.get(key);

    if (memRecord) {
        if (now - memRecord.firstRequest > windowMs) {
            // Window expired, reset
            rateLimitStore.set(key, { count: 1, firstRequest: now });
            return true;
        }

        if (memRecord.count >= limit) {
            return false;
        }

        memRecord.count++;
        return true;
    }

    // Check localStorage for persistence across reloads
    const storageKey = `rate_limit_${key}`;
    try {
        const record = localStorage.getItem(storageKey);
        if (record) {
            const { count, firstRequest } = JSON.parse(record);

            if (now - firstRequest > windowMs) {
                // Window expired
                const newRecord = { count: 1, firstRequest: now };
                rateLimitStore.set(key, newRecord);
                localStorage.setItem(storageKey, JSON.stringify(newRecord));
                return true;
            }

            if (count >= limit) {
                // Also store in memory to prevent localStorage clear bypass
                rateLimitStore.set(key, { count, firstRequest });
                return false;
            }

            const newRecord = { count: count + 1, firstRequest };
            rateLimitStore.set(key, newRecord);
            localStorage.setItem(storageKey, JSON.stringify(newRecord));
            return true;
        }
    } catch {
        // localStorage unavailable, rely on memory only
    }

    // First request
    const newRecord = { count: 1, firstRequest: now };
    rateLimitStore.set(key, newRecord);
    try {
        localStorage.setItem(storageKey, JSON.stringify(newRecord));
    } catch {
        // Ignore localStorage errors
    }
    return true;
}
