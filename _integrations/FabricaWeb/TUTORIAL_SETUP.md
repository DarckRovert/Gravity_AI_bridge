# 🍰 Tutorial de Configuración — Dulces Momentos

Guía paso a paso para configurar todo lo que el proyecto necesita correr en producción.
**Tiempo estimado total: 30–45 minutos.**

---

## 📋 Índice

1. [Configurar `.env.local`](#1-configurar-envlocal)
2. [Desplegar Reglas de Firestore](#2-desplegar-reglas-de-firestore)
3. [Crear el Usuario Administrador](#3-crear-el-usuario-administrador)
4. [Activar Notificaciones Push (FCM)](#4-activar-notificaciones-push-fcm)
5. [Integrar Pago con Tarjeta (Culqi)](#5-integrar-pago-con-tarjeta-culqi)
6. [Desplegar en Netlify](#6-desplegar-en-netlify)

---

## 1. Configurar `.env.local`

Crea el archivo `.env.local` en la raíz de `pastelito-next/` si no existe:

```bash
# ── FIREBASE ──────────────────────────────────────────────────────────────────
NEXT_PUBLIC_FIREBASE_API_KEY=AIza...
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=tu-proyecto.firebaseapp.com
NEXT_PUBLIC_FIREBASE_PROJECT_ID=tu-proyecto
NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET=tu-proyecto.appspot.com
NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID=123456789012
NEXT_PUBLIC_FIREBASE_APP_ID=1:123456789012:web:abc123

# ── FCM (Notificaciones Push) ─────────────────────────────────────────────────
NEXT_PUBLIC_FIREBASE_VAPID_KEY=BNfg...    # Ver Paso 4

# ── CULQI (Pago con Tarjeta) ──────────────────────────────────────────────────
NEXT_PUBLIC_CULQI_PUBLIC_KEY=pk_test_...  # Ver Paso 5
CULQI_SECRET_KEY=sk_test_...              # Ver Paso 5 (NUNCA public)
```

> ⚠️ Nunca subas `.env.local` a GitHub. Está en `.gitignore` por diseño.

---

## 2. Desplegar Reglas de Firestore

Las reglas de seguridad protegen tu base de datos. Sin desplegarlas, Firebase usa
reglas permisivas por defecto (cualquiera puede leer/borrar pedidos).

### Requisito: Firebase CLI

Si no lo tienes instalado:
```bash
npm install -g firebase-tools
```

### Pasos

```bash
# 1. Autentícate con tu cuenta de Google
firebase login

# 2. Asocia el proyecto (ejecuta desde la raíz de pastelito-next)
firebase use tu-proyecto-id

# 3. Despliega SOLO las reglas (no toca nada más)
firebase deploy --only firestore:rules
```

✅ **Verificación:** Ve a [Firebase Console](https://console.firebase.google.com) → tu proyecto → Firestore Database → Rules. Debes ver las reglas del archivo `firestore.rules`.

---

## 3. Crear el Usuario Administrador

El sistema de login del admin usa Firebase Authentication.

### Pasos en Firebase Console

1. Ve a [Firebase Console](https://console.firebase.google.com) → tu proyecto
2. En el menú izquierdo → **Authentication**
3. Clic en **"Get started"** si no está activado
4. Pestaña **"Sign-in method"** → Habilita **Email/Password**
5. Pestaña **"Users"** → Clic en **"Add user"**
6. Ingresa:
   - Email: `admin@dulcesmoment0s.com` (o el que prefieras)
   - Password: Una contraseña segura (mínimo 8 caracteres)
7. Clic en **"Add user"**

### Usar en la app

En el formulario de login `/admin`, ingresa el email y contraseña que acabas de crear.

> 💡 Si las variables de Firebase están en `.env.local`, el login usa Firebase Auth.  
> Si no están configuradas, usa el sistema de respaldo con la clave hardcodeada.

---

## 4. Activar Notificaciones Push (FCM)

Las notificaciones push avisan al administrador cuando llega un nuevo pedido y al cliente cuando su pedido cambia de estado.

### Paso 4.1 — Obtener la VAPID Key

1. Ve a [Firebase Console](https://console.firebase.google.com) → tu proyecto
2. Clic en el ⚙️ (engranaje) → **"Project settings"**
3. Pestaña **"Cloud Messaging"**
4. En la sección **"Web Push certificates"** → clic en **"Generate key pair"**
5. Copia la **"Key pair"** generada

### Paso 4.2 — Agregar al `.env.local`

```bash
NEXT_PUBLIC_FIREBASE_VAPID_KEY=BNfg_aqui_va_tu_vapid_key_larga...
```

### Paso 4.3 — Habilitar la API de Cloud Messaging

1. En Firebase Console → **Build** → **Cloud Messaging**
2. Asegúrate de que la API esté habilitada (debería estarlo por defecto)

### Paso 4.4 — Configurar el Service Worker

Verifica que exista el archivo `public/firebase-messaging-sw.js`. Si no existe, créalo:

```js
// public/firebase-messaging-sw.js
importScripts('https://www.gstatic.com/firebasejs/10.0.0/firebase-app-compat.js');
importScripts('https://www.gstatic.com/firebasejs/10.0.0/firebase-messaging-compat.js');

firebase.initializeApp({
  apiKey: "TU_API_KEY",
  authDomain: "tu-proyecto.firebaseapp.com",
  projectId: "tu-proyecto",
  storageBucket: "tu-proyecto.appspot.com",
  messagingSenderId: "123456789012",
  appId: "1:123456789012:web:abc123",
});

const messaging = firebase.messaging();

// Manejar mensajes en background
messaging.onBackgroundMessage((payload) => {
  self.registration.showNotification(payload.notification.title, {
    body: payload.notification.body,
    icon: '/img/icon-192.png',
  });
});
```

✅ **Resultado:** Al entrar a la web por primera vez (después de 30 segundos), aparecerá el banner de suscripción a notificaciones.

---

## 5. Integrar Pago con Tarjeta (Culqi)

Culqi es la pasarela de pago peruana. Permite cobrar con cualquier tarjeta Visa, Mastercard o Amex.

### Paso 5.1 — Crear tu cuenta Culqi

1. Regístrate en [https://culqi.com](https://culqi.com)
2. Completa la verificación de tu empresa/persona jurídica
3. Una vez aprobado, tendrás acceso al **Dashboard de Culqi**

### Paso 5.2 — Obtener las API Keys

1. En el Dashboard de Culqi → **Desarrolladores** → **Llaves de API**
2. Verás dos entornos: **Test** y **Producción**
3. Para pruebas, copia las llaves de **Test**:
   - **Llave pública** (empieza con `pk_test_...`)
   - **Llave secreta** (empieza con `sk_test_...`)

### Paso 5.3 — Agregar al `.env.local`

```bash
NEXT_PUBLIC_CULQI_PUBLIC_KEY=pk_test_aqui_va_tu_llave_publica
CULQI_SECRET_KEY=sk_test_aqui_va_tu_llave_secreta
```

### Paso 5.4 — Probar el flujo de pago

Para pruebas en Culqi, usa estas tarjetas de test:
| Tarjeta | Número | CVV | Fecha |
|---------|--------|-----|-------|
| Visa (aprobada) | `4111111111111111` | `123` | `09/25` |
| Mastercard (aprobada) | `5111111111111118` | `123` | `09/25` |
| Visa (declinada) | `4000000000000002` | `123` | `09/25` |

✅ **Resultado:** En el Checkout, al seleccionar "Tarjeta" aparecerá el botón de Culqi con el precio final. Al hacer clic se abre el modal de pago.

### Paso 5.5 — Cambiar a producción

Cuando tengas la cuenta aprobada para producción:
1. Reemplaza las llaves `pk_test_...` y `sk_test_...` por las de producción
2. Redespliega en Netlify

---

## 6. Desplegar en Netlify

### Opción A: Via Git (Recomendado)

1. Sube el proyecto a GitHub (si no lo has hecho):
   ```bash
   git add .
   git commit -m "feat: mejoras completas v2.0"
   git push origin main
   ```

2. En [Netlify](https://netlify.com) → **Add new site** → **Import from Git**
3. Selecciona tu repositorio
4. Configuración de build:
   - **Base directory:** `pastelito-next`
   - **Build command:** `npm run build`
   - **Publish directory:** `pastelito-next/.next`

5. Ve a **Site settings** → **Environment variables** y agrega **todas** las variables de tu `.env.local`

### Opción B: Build local + arrastrar carpeta

```bash
cd pastelito-next
npm run build
```

Luego arrastra la carpeta `.next` al panel de Netlify.

### Variables de entorno en Netlify

Agrega todas estas en Netlify → Site settings → Environment variables:

| Variable | Descripción |
|----------|-------------|
| `NEXT_PUBLIC_FIREBASE_API_KEY` | Firebase API Key |
| `NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN` | Firebase Auth Domain |
| `NEXT_PUBLIC_FIREBASE_PROJECT_ID` | Firebase Project ID |
| `NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET` | Firebase Storage |
| `NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID` | Firebase Sender ID |
| `NEXT_PUBLIC_FIREBASE_APP_ID` | Firebase App ID |
| `NEXT_PUBLIC_FIREBASE_VAPID_KEY` | VAPID key para FCM |
| `NEXT_PUBLIC_CULQI_PUBLIC_KEY` | Culqi public key |
| `CULQI_SECRET_KEY` | Culqi secret key (⚠️ no exponer) |

---

## ✅ Checklist Final

- [ ] `.env.local` creado con todas las variables
- [ ] Reglas Firestore desplegadas (`firebase deploy --only firestore:rules`)
- [ ] Usuario admin creado en Firebase Console → Authentication
- [ ] VAPID key generada y en `.env.local`
- [ ] Service worker FCM creado en `public/firebase-messaging-sw.js`
- [ ] Cuenta Culqi creada y API keys en `.env.local`
- [ ] Variables de entorno en Netlify configuradas
- [ ] Sitio desplegado correctamente

---

*Tutorial generado el 03/03/2026 · Proyecto: Dulces Momentos · Arquitecto: DarckRovert*
