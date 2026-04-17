"use client";

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { checkRateLimit } from '@/lib/auth';
import { isFirebaseConfigured } from '@/lib/firebase';
import { firebaseAdminLogin, onAdminAuthStateChanged } from '@/lib/firebaseAuth';
// Legacy fallback
import { hashPassword, generateSessionToken, isValidSessionToken } from '@/lib/auth';

// ─── Legacy Keys (only used when Firebase is not configured) ─────────────────
const SESSION_KEY = 'dm_admin_session';
const PWD_KEY = 'dm_admin_pwd';
const DEFAULT_HASH = 'cd4ba2d8fccb75a30c84f9f4fc697040f7e93c8f8a0198fdb73414bc3e73f0e2';

function getLegacyHash(): string {
    if (typeof window === 'undefined') return DEFAULT_HASH;
    return localStorage.getItem(PWD_KEY) || DEFAULT_HASH;
}

export default function AdminLogin() {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const [useFirebase] = useState(() => isFirebaseConfigured());
    const router = useRouter();

    useEffect(() => {
        if (useFirebase) {
            // Firebase Auth: subscribe to auth state
            const unsub = onAdminAuthStateChanged((user) => {
                if (user) router.push('/admin/dashboard');
            });
            return unsub;
        } else {
            // Legacy: validate localStorage session token
            const session = localStorage.getItem(SESSION_KEY);
            if (isValidSessionToken(session)) {
                router.push('/admin/dashboard');
            } else if (session) {
                localStorage.removeItem(SESSION_KEY);
            }
        }
    }, [router, useFirebase]);

    // ── Firebase Auth Login ────────────────────────────────────────────────────
    const handleFirebaseLogin = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        setLoading(true);

        if (!checkRateLimit('admin_login', 5, 60000)) {
            setError('Demasiados intentos. Espera 1 minuto.');
            setLoading(false);
            return;
        }

        const result = await firebaseAdminLogin(email, password);
        if (result.success) {
            router.push('/admin/dashboard');
        } else {
            setError(result.error ?? 'Error al iniciar sesión.');
            setPassword('');
        }
        setLoading(false);
    };

    // ── Legacy (localStorage) Login ───────────────────────────────────────────
    const handleLegacyLogin = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        setLoading(true);

        if (!checkRateLimit('admin_login', 5, 60000)) {
            setError('Demasiados intentos. Espera 1 minuto.');
            setLoading(false);
            return;
        }

        const targetHash = getLegacyHash();
        const inputHash = await hashPassword(password);

        if (inputHash === targetHash) {
            const token = generateSessionToken();
            localStorage.setItem(SESSION_KEY, token);
            router.push('/admin/dashboard');
        } else {
            setError('Contraseña incorrecta.');
            setPassword('');
        }
        setLoading(false);
    };

    const handleSubmit = useFirebase ? handleFirebaseLogin : handleLegacyLogin;

    return (
        <main className="min-h-screen bg-dash-bg flex items-center justify-center p-4 font-poppins">
            <div className="bg-dash-card border border-dash-border rounded-3xl p-10 max-w-sm w-full text-center shadow-2xl animate-fade-up">
                <div className="text-4xl mb-4 animate-bounce">🧁</div>
                <h1 className="text-3xl font-playfair font-bold text-secondary mb-1">Panel Admin</h1>
                <p className="text-gray-400 mb-1 font-light text-sm">Dulces Momentos CFO</p>
                {useFirebase ? (
                    <span className="inline-block mb-6 text-xs bg-green-900/40 text-green-400 border border-green-800 rounded-full px-3 py-0.5">
                        🔒 Firebase Auth
                    </span>
                ) : (
                    <span className="inline-block mb-6 text-xs bg-yellow-900/40 text-yellow-400 border border-yellow-800 rounded-full px-3 py-0.5">
                        ⚠️ Auth Local (configura Firebase)
                    </span>
                )}

                <form onSubmit={handleSubmit} className="space-y-4">
                    {/* Email field — shown only for Firebase auth */}
                    {useFirebase && (
                        <input
                            type="email"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            placeholder="admin@dulcesmomentos.com"
                            className="w-full bg-dash-bg border-2 border-dash-border rounded-xl px-4 py-3 text-white text-center focus:outline-none focus:border-secondary transition-all"
                            disabled={loading}
                            required
                        />
                    )}

                    <input
                        type="password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        placeholder="••••••••"
                        className="w-full bg-dash-bg border-2 border-dash-border rounded-xl px-4 py-3 text-white text-center tracking-widest focus:outline-none focus:border-secondary transition-all"
                        disabled={loading}
                        required
                    />

                    {error && <p className="text-red-400 text-sm animate-shake">{error}</p>}

                    <button
                        type="submit"
                        disabled={loading}
                        className="w-full bg-gradient-to-r from-secondary to-secondary/80 text-dash-bg py-3 rounded-xl font-bold hover:shadow-[0_0_20px_rgba(212,175,55,0.4)] transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        {loading ? 'Verificando...' : 'INGRESAR'}
                    </button>
                </form>

                <p className="mt-8 text-xs text-gray-500 uppercase tracking-widest">Acceso Restringido &bull; Seguro</p>
                {!useFirebase && (
                    <p className="mt-2 text-xs text-gray-600">
                        Contraseña por defecto: <span className="text-secondary font-mono">dulces2026</span>
                    </p>
                )}
            </div>
        </main>
    );
}
