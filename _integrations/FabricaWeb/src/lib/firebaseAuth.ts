/**
 * 🔐 Firebase Authentication Module — Dulces Momentos
 *
 * Handles admin authentication via Firebase Auth (email/password).
 * Falls back to the legacy localStorage session if Firebase is not configured.
 */

import {
    signInWithEmailAndPassword,
    signOut,
    onAuthStateChanged,
    User,
    AuthError,
} from 'firebase/auth';
import { auth, isFirebaseConfigured } from './firebase';

// ── Types ─────────────────────────────────────────────────────────────────────

export interface AuthResult {
    success: boolean;
    error?: string;
    user?: User;
}

// ── Firebase Auth Helpers ──────────────────────────────────────────────────────

/**
 * Sign in an admin using Firebase Authentication (email + password).
 */
export async function firebaseAdminLogin(email: string, password: string): Promise<AuthResult> {
    if (!isFirebaseConfigured()) {
        return { success: false, error: 'Firebase no está configurado.' };
    }

    try {
        const credential = await signInWithEmailAndPassword(auth, email, password);
        return { success: true, user: credential.user };
    } catch (err) {
        const authError = err as AuthError;
        const messages: Record<string, string> = {
            'auth/invalid-credential': 'Email o contraseña incorrectos.',
            'auth/user-not-found': 'No existe una cuenta con ese email.',
            'auth/wrong-password': 'Contraseña incorrecta.',
            'auth/too-many-requests': 'Demasiados intentos. Espera unos minutos.',
            'auth/user-disabled': 'Esta cuenta ha sido desactivada.',
        };
        return {
            success: false,
            error: messages[authError.code] ?? 'Error de autenticación. Intenta de nuevo.',
        };
    }
}

/**
 * Sign out the current admin from Firebase.
 */
export async function firebaseAdminLogout(): Promise<void> {
    try {
        await signOut(auth);
    } catch {
        // Ignore sign-out errors silently
    }
}

/**
 * Subscribe to auth state changes. Returns an unsubscribe function.
 */
export function onAdminAuthStateChanged(callback: (user: User | null) => void): () => void {
    return onAuthStateChanged(auth, callback);
}

/**
 * Get the currently authenticated user (synchronous snapshot).
 */
export function getCurrentAdmin(): User | null {
    return auth.currentUser;
}

/**
 * Check if the current user is authenticated.
 */
export function isAdminAuthenticated(): boolean {
    return auth.currentUser !== null;
}
