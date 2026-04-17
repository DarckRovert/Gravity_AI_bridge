# 🍰 Dulces Momentos — Pastelito AI (God Mode v6.0)

> **"La primera pastelería gestionada por una Inteligencia Artificial 100% Autónoma."**

**Dulces Momentos** es una e-commerce de pastelería artesanal con un chatbot administrador autónomo capaz de gestionar la tienda, diseñar la interfaz, analizar finanzas y proteger el sistema mediante lenguaje natural.

🌐 **Ver en vivo:** [dulcesmoment0s.netlify.app](https://dulcesmoment0s.netlify.app)

---

## 🏢 Información del Negocio

| Campo | Detalle |
|-------|---------|
| **Negocio** | Dulces Momentos |
| **Rubro** | Pastelería Artesanal |
| **Ubicación** | Santiago de Surco, Lima, Perú |
| **WhatsApp** | [+51 965 968 723](https://wa.me/51965968723) |
| **Horario** | Lun–Sáb, 09:00–20:00 |

---

## ✨ Características Principales

### 🛒 Tienda Online & Checkout
- Catálogo con filtros por categoría + búsqueda en tiempo real + toggle Grid/Lista
- Carrito con subtotal por ítem, IGV (18%) y animaciones
- **Checkout Wizard (3 pasos):** Envío → Regalo/Pago → Revisión con barra de progreso
- Geolocalización (OpenStreetMap) para autocompletar la dirección de entrega
- Validación en tiempo real del teléfono peruano
- Date picker: bloquea domingos y fechas que el admin marca como llenas
- **Cupones** de descuento (% o monto fijo)
- **Puntos de Fidelidad 🍬** — 1 S/ = 1 punto, banner de canje en el Checkout
- **Pago con Tarjeta vía Culqi** (Visa, Mastercard, Amex) — activo con API keys

### 🤖 Chatbot "Pastelito" — God Mode v6.0
- **Motor NLP local** — 100% simbólico, sin dependencias externas de IA
- **Modo Cliente:** Recomendaciones, FAQ, venta cruzada, loose search ("¿Quisiste decir...?")
- **Modo Admin (AI CEO):**
  - Gestión de productos, cupones, temas, secciones y zonas
  - Análisis financiero: reporte ejecutivo, ranking, anomalías, predicciones
  - **Calendario de Disponibilidad:** bloquea/desbloquea fechas por chat
  - Rate limiting (1 msg/s) + ventana minimizable en móvil
- Encerrado en `ErrorBoundary` para que un error no tumbe la página

### 📊 Dashboard Pro (Admin)
- Login via **Firebase Authentication** (fallback seguro si no hay env vars)
- **6 Tabs**: Resumen · Productos · Pedidos (pipeline) · Cupones · Tema · Analytics
- Code splitting: cada tab carga solo cuando se visita (next/dynamic)

### 🔔 Notificaciones Push (FCM)
- Banner de suscripción no intrusivo (aparece a los 30s)
- Notificaciones en background via Firebase Cloud Messaging
- Activo con `NEXT_PUBLIC_FIREBASE_VAPID_KEY`

### 🌐 Coleccionables Digitales (Web3 / NFT)
- Sección "Proof of Cake" en la landing page con 3 pasos explicativos
- NFTCard con tooltip "¿Qué es un NFT?" + badge de red animado
- Switcher interactivo Polygon Amoy ↔ Mainnet

### ⭐ Reseñas Verificadas
- Guardadas en Firestore, verificadas con `orderId` real
- Badge ✅ Verificado solo para compradores reales

---

## 🛠️ Stack Tecnológico

| Área | Tecnología |
|------|-----------|
| Framework | Next.js 16 (App Router) |
| UI | React 19 + TailwindCSS v4 |
| Lenguaje | TypeScript v5 — 0 errores, 0 `any` |
| AI/NLP | PastelitoEngine (NLP simbólico) + LocalBrain (Naive Bayes) |
| Backend | Firebase/Firestore (fallback localStorage automático) |
| Auth | Firebase Authentication |
| Push | Firebase Cloud Messaging (FCM) |
| Pagos | Culqi (pasarela peruana) |
| Web3 | Ethers.js + MetaMask (Polygon Amoy Testnet) |
| Tests | Vitest — 19/19 ✅ |
| Deploy | Netlify |

---

## 🚀 Inicio Rápido (Desarrollo Local)

```bash
# 1. Instalar dependencias
cd pastelito-next
npm install

# 2. Configurar variables de entorno
cp .env.local.example .env.local
# → Edita .env.local con tus keys de Firebase y Culqi

# 3. Correr en desarrollo
npm run dev

# 4. Verificar calidad de código
npx tsc --noEmit   # → 0 errores
npx vitest run     # → 19/19 tests ✅
```

---

## 🔑 Comandos God Mode (Admin)

| Intención | Ejemplo | Acción |
|-----------|---------|--------|
| **Precio** | *"Sube el Pionono a 80"* | Actualiza precio |
| **Stock** | *"El Cheesecake está agotado"* | Desactiva el producto |
| **Diseño** | *"Modo Navidad"* | Cambia colores y banner |
| **Cupón** | *"Crea VERANO20 del 20%"* | Genera código de descuento |
| **Reporte** | *"Reporte ejecutivo"* | Ventas, ranking, anomalías |
| **Predicción** | *"¿Cuánto vendo mañana?"* | Estimación por patrones |
| **Calendario** | *"Bloquea el 15 de marzo"* | Fecha indisponible en Checkout |

---

## 📂 Documentación

| Archivo | Descripción |
|---------|-------------|
| **[TUTORIAL_SETUP.md](./TUTORIAL_SETUP.md)** | ⭐ **Empieza aquí** — Configuración de Firebase, FCM, Culqi y Netlify |
| **[DEPLOY.md](./DEPLOY.md)** | Build y deploy técnico |
| **[ARCHITECTURE.md](./ARCHITECTURE.md)** | Arquitectura del sistema |
| **[BLOCKCHAIN.md](./BLOCKCHAIN.md)** | Módulo NFT y Web3 |
| **[MANUAL.md](./MANUAL.md)** | Manual completo de usuario |
| **[GUIA_ADMIN.md](./GUIA_ADMIN.md)** | Panel de administración |
| **[GUIA_HOSTING.md](./GUIA_HOSTING.md)** | Opciones de hosting |

---

## 👨‍💻 Créditos

**Arquitecto y Desarrollador Principal:**
Rodrigo Alejandro Vega Rojas (**DarckRovert**)

> *"La tecnología debe ser mágica, pero sobre todo, útil."*

---
© 2026 Dulces Momentos. Todos los derechos reservados.
