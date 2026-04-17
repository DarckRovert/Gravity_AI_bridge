# 🗺️ Diagrama de Arquitectura — Pastelito AI v5.0

## Flujo Principal

```mermaid
flowchart TD
    User(["👤 Usuario / Admin"]) -->|texto o voz| Chatbot["🤖 Chatbot.tsx"]

    Chatbot -->|modo cliente| FallbackChain
    Chatbot -->|modo admin / CEO| PastelitoEngine

    subgraph AI_LOCAL["🧠 Stack IA Local (100% Navegador)"]
        FallbackChain["FallbackChain (orquestador)"]
        FallbackChain -->|"1️⃣ similitud semántica"| SemanticEngine["SemanticEngine\n(transformers.js\nall-MiniLM-L6-v2)"]
        FallbackChain -->|"2️⃣ Naive Bayes fallback"| LocalBrain["LocalBrain\n(Naive Bayes)"]
        FallbackChain -->|"3️⃣ final fallback"| WA["📱 WhatsApp"]
        SemanticEngine --- KB["chatbot-kb.ts\n120+ entradas"]
    end

    subgraph CEO["👔 CEO Mode (adminBrain.ts)"]
        PastelitoEngine["PastelitoEngine\n(NLP Simbólico, 60+ intents)"]
        PastelitoEngine --> AdminBrain["AdminBrain v3.0"]
        AdminBrain --> Report["📊 Smart Report"]
        AdminBrain --> Ranking["🏆 Product Ranking"]
        AdminBrain --> Anomalies["⚠️ Anomaly Detection"]
        AdminBrain --> Insights["💡 Actionable Insights"]
        AdminBrain --> Demand["🔮 Demand Prediction"]
    end

    PastelitoEngine --> AdminActions["adminActions.ts"]
    AdminActions --> Context["SiteConfigContext\n(localStorage + Gun.js P2P)"]
    Context --> UI["🖥️ Componentes React"]
```

---

## Capa de Datos

```mermaid
flowchart LR
    Checkout["🛒 Checkout"] -->|createOrder| Firestore[("🔥 Firestore")]
    Checkout -->|fallback| LS[("💾 localStorage")]

    Firestore -->|onSnapshot| Dashboard["📊 Dashboard"]
    Firestore -->|getOrderById| Tracker["📍 /tracker"]
    LS -->|getOrdersSync| Dashboard

    Context["SiteConfigContext"] -->|dm_config| LS
    Context -->|sync| Gun["⚡ Gun.js P2P"]
```

---

## Estructura de Archivos Clave

```
src/
├── app/
│   ├── admin/dashboard/    → Dashboard Pro (6 tabs)
│   ├── checkout/           → Checkout + Confirm
│   └── tracker/            → Rastreo en vivo
├── components/
│   ├── Chatbot.tsx          → UI del chatbot
│   └── dashboard/          → ProductManager, OrderPipeline, etc.
├── data/
│   ├── products.ts          → Catálogo de productos
│   └── chatbot-kb.ts       → Knowledge Base (120+ entradas)
├── hooks/
│   └── useChatActions.ts   → Acciones del chatbot (CEO + cliente)
└── lib/
    ├── ai/
    │   ├── semanticEngine.ts  → 🆕 IA semántica (transformers.js)
    │   ├── localBrain.ts      → Naive Bayes classifier
    │   ├── fallbackChain.ts   → Orquestador de respuestas
    │   └── visionBrain.ts     → MobileNet (Proof of Cake)
    ├── adminBrain.ts          → CEO analytics v3.0
    ├── pastelitoEngine.ts     → NLP simbólico
    ├── firebase.ts            → Firebase init
    └── firebaseOrders.ts      → CRUD pedidos Firestore
```

---

## Cadena de Respuesta del Chatbot

```mermaid
flowchart LR
    Q["❓ Pregunta del cliente"] --> S{"Semantic Engine\n> 0.55 confianza?"}
    S -->|Sí| R1["✅ Respuesta directa\ndel Knowledge Base"]
    S -->|No| L{"LocalBrain\nscore > -20?"}
    L -->|Sí| R2["✅ Respuesta por\nintención Naive Bayes"]
    L -->|No| R3["📱 Redirigir\na WhatsApp"]
```
