# 🚀 Guía de Despliegue — Dulces Momentos v6.0

Pasos técnicos para desplegar el proyecto en producción.

> ⭐ Para la configuración de Firebase, FCM y Culqi, lee primero **[TUTORIAL_SETUP.md](./TUTORIAL_SETUP.md)**.

---

## 1. Requisitos

- **Node.js** v20+
- **npm** v10+
- Cuenta Firebase (Firestore + Authentication + Cloud Messaging)
- Cuenta Culqi (para pagos con tarjeta)
- Cuenta Netlify (para deploy)

---

## 2. Variables de Entorno

Crea `.env.local` en la raíz del proyecto (usa `.env.local.example` como plantilla):

```env
# ── FIREBASE ──────────────────────────────────────────────────────────────────
NEXT_PUBLIC_FIREBASE_API_KEY=AIza...
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=tu-proyecto.firebaseapp.com
NEXT_PUBLIC_FIREBASE_PROJECT_ID=tu-proyecto
NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET=tu-proyecto.appspot.com
NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID=123456789012
NEXT_PUBLIC_FIREBASE_APP_ID=1:123456789012:web:abc123

# ── FCM — Notificaciones Push ─────────────────────────────────────────────────
NEXT_PUBLIC_FIREBASE_VAPID_KEY=BNfg...

# ── CULQI — Pago con Tarjeta ──────────────────────────────────────────────────
NEXT_PUBLIC_CULQI_PUBLIC_KEY=pk_test_...
CULQI_SECRET_KEY=sk_test_...         # ⚠️ Solo server-side, nunca exponer
```

> Sin Firebase, el sistema usa `localStorage` como fallback automático.
> Sin Culqi, el botón de tarjeta muestra "Próximamente" en lugar de ocultarse.

---

## 3. Build y Verificación

```bash
# Instalar dependencias
npm install

# Verificar tipos (debe ser 0 errores)
npx tsc --noEmit

# Correr tests (debe ser 19/19)
npx vitest run

# Build de producción
npm run build
```

---

## 4. Despliegue en Netlify

### Opción A — Via Git (Recomendado)

1. Conecta tu repo en [netlify.com](https://netlify.com) → Add new site → Import from Git
2. Configuración de build:
   - **Base directory:** `pastelito-next`
   - **Build command:** `npm run build`
   - **Publish directory:** `pastelito-next/.next`
3. Agrega todas las variables de entorno en **Site settings → Environment Variables**

### Opción B — Build local

```bash
npm run build
# Arrastra la carpeta .next al panel de Netlify
```

---

## 5. Configuración Post-Deploy en Firebase

### Desplegar reglas de Firestore

```bash
npm install -g firebase-tools
firebase login
firebase use tu-proyecto-id
firebase deploy --only firestore:rules
```

Las reglas del archivo `firestore.rules` aseguran que:
- Solo usuarios autenticados (admin) pueden leer y modificar pedidos
- Cualquier persona puede crear un pedido
- Las reseñas requieren un `orderId` válido

### Crear usuario admin

1. Firebase Console → Authentication → Sign-in method → Habilitar Email/Password
2. Users → Add user → ingresa email y contraseña
3. Esas credenciales se usan en `/admin` para iniciar sesión

---

## 6. Verificación Post-Deploy

- [ ] `/admin` → Login con Firebase Auth funciona
- [ ] Dashboard → 6 tabs cargan correctamente
- [ ] Chatbot en modo admin: `"Reporte ejecutivo"` devuelve informe
- [ ] `"Bloquea el 20 de marzo"` → fecha bloqueada en Checkout
- [ ] Pedido de prueba → aparece en tab Pedidos
- [ ] Notificación push → banner aparece a los 30s
- [ ] Checkout → tarjeta de prueba Culqi procesa correctamente
- [ ] `/menu` → filtros, búsqueda y toggle Grid/Lista funcionan
- [ ] NFT Section en la página principal visible

---

## 7. Tarjetas de Prueba Culqi (Test)

| Tarjeta | Número | CVV | Fecha | Resultado |
|---------|--------|-----|-------|-----------|
| Visa | `4111111111111111` | `123` | `09/25` | ✅ Aprobada |
| Mastercard | `5111111111111118` | `123` | `09/25` | ✅ Aprobada |
| Visa | `4000000000000002` | `123` | `09/25` | ❌ Declinada |

---

*Arquitecto: Rodrigo Alejandro Vega Rojas (DarckRovert) · v6.0 · 03/03/2026*
