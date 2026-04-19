/**
 * 🔧 Environment Variables — Dulces Momentos
 *
 * Centralized, typed access to all env vars.
 * Fails fast with clear error messages if required vars are missing.
 */

function required(key: string): string {
    const val = process.env[key];
    if (!val) {
        // In development, show a clear warning but don't crash hard
        if (process.env.NODE_ENV === 'development') {
            console.warn(`⚠️  Missing env var: ${key}. Check .env.local`);
            return '';
        }
        // In production, log but return empty (Firebase has its own fallback)
        console.error(`❌ Missing required env var: ${key}`);
        return '';
    }
    return val;
}

function optional(key: string, fallback = ''): string {
    return process.env[key] ?? fallback;
}

export const env = {
    // ── Firebase ────────────────────────────────────────────────────────────
    firebase: {
        apiKey: optional('NEXT_PUBLIC_FIREBASE_API_KEY'),
        authDomain: optional('NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN'),
        projectId: optional('NEXT_PUBLIC_FIREBASE_PROJECT_ID'),
        storageBucket: optional('NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET'),
        messagingSenderId: optional('NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID'),
        appId: optional('NEXT_PUBLIC_FIREBASE_APP_ID'),
    },

    // ── App ─────────────────────────────────────────────────────────────────
    app: {
        whatsapp: optional('NEXT_PUBLIC_WHATSAPP', '+51965968723'),
        businessName: optional('NEXT_PUBLIC_BUSINESS_NAME', 'Dulces Momentos'),
        deployUrl: optional('NEXT_PUBLIC_DEPLOY_URL', 'https://dulcesmomentosp.netlify.app'),
    },

    // ── Web3 ────────────────────────────────────────────────────────────────
    web3: {
        walletConnectProjectId: optional('NEXT_PUBLIC_WALLETCONNECT_PROJECT_ID'),
    },

    // ── Flags ───────────────────────────────────────────────────────────────
    isFirebaseConfigured: (): boolean => {
        return !!env.firebase.apiKey && env.firebase.apiKey !== 'YOUR_API_KEY';
    },
    isDevelopment: process.env.NODE_ENV === 'development',
    isProduction: process.env.NODE_ENV === 'production',
} as const;

export default env;
