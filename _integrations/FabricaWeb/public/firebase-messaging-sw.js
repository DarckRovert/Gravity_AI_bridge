// public/firebase-messaging-sw.js
// ── Firebase Cloud Messaging Service Worker ──────────────────────────────────
// Este archivo debe estar en la raíz de /public/ para que el browser lo
// registre como service worker. Reemplaza los valores con los de tu proyecto.

importScripts('https://www.gstatic.com/firebasejs/10.7.1/firebase-app-compat.js');
importScripts('https://www.gstatic.com/firebasejs/10.7.1/firebase-messaging-compat.js');

firebase.initializeApp({
    // ⚠️ REEMPLAZA ESTOS VALORES con los de tu .env.local
    // Nota: el SW no tiene acceso a process.env, usar los valores literales aquí.
    apiKey: "REEMPLAZA_CON_TU_API_KEY",
    authDomain: "REEMPLAZA.firebaseapp.com",
    projectId: "REEMPLAZA",
    storageBucket: "REEMPLAZA.appspot.com",
    messagingSenderId: "REEMPLAZA",
    appId: "REEMPLAZA",
});

const messaging = firebase.messaging();

// ── Notificaciones en Background (cuando la app está minimizada/cerrada) ──────
messaging.onBackgroundMessage((payload) => {
    console.log('[SW] Mensaje recibido en background:', payload);

    const title = payload.notification?.title ?? '🍰 Dulces Momentos';
    const body = payload.notification?.body ?? 'Tienes una notificación nueva.';
    const icon = payload.notification?.icon ?? '/img/icon-192.png';
    const badge = '/img/icon-192.png';

    self.registration.showNotification(title, { body, icon, badge });
});
