"use client";

/**
 * 🔥 Firebase Configuration - Dulces Momentos
 *
 * SETUP INSTRUCTIONS:
 * 1. Go to https://console.firebase.google.com
 * 2. Create / open your "dulces-momentos" project
 * 3. Enable Firestore + Authentication (Email/Password provider)
 * 4. Add a Web App and copy the config values to .env.local
 * 5. Deploy firestore.rules: firebase deploy --only firestore:rules
 */

import { initializeApp, getApps, FirebaseApp } from 'firebase/app';
import { getFirestore, Firestore } from 'firebase/firestore';
import { getAuth, Auth } from 'firebase/auth';

// ========================
// 🔧 FIREBASE CONFIG
// ========================
// Replace these with your real Firebase project values
const firebaseConfig = {
    apiKey: process.env.NEXT_PUBLIC_FIREBASE_API_KEY || "YOUR_API_KEY",
    authDomain: process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN || "dulces-momentos.firebaseapp.com",
    projectId: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID || "dulces-momentos",
    storageBucket: process.env.NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET || "dulces-momentos.appspot.com",
    messagingSenderId: process.env.NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID || "000000000000",
    appId: process.env.NEXT_PUBLIC_FIREBASE_APP_ID || "1:000000000000:web:0000000000000000"
};

// ========================
// 🚀 INITIALIZATION
// ========================

let app: FirebaseApp;
let firestore: Firestore;
let auth: Auth;

// Prevent multiple initializations in Next.js hot reload
if (getApps().length === 0) {
    app = initializeApp(firebaseConfig);
} else {
    app = getApps()[0];
}

firestore = getFirestore(app);
auth = getAuth(app);

// ========================
// 🔍 HELPERS
// ========================

/**
 * Check if Firebase is properly configured (not using placeholder values)
 */
export function isFirebaseConfigured(): boolean {
    return firebaseConfig.apiKey !== "YOUR_API_KEY" &&
        !!process.env.NEXT_PUBLIC_FIREBASE_API_KEY;
}

/**
 * Get the active data source indicator
 * Returns 'firebase' if configured, 'local' if using localStorage fallback
 */
export function getDataSource(): 'firebase' | 'local' {
    return isFirebaseConfigured() ? 'firebase' : 'local';
}

export { app, app as firebaseApp, firestore, auth };
export default firestore;
