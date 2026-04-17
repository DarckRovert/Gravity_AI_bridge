# 👑 Guía de Administración (Sin Código) — v6.0
### Dulces Momentos - Panel de Control

Esta guía te enseña a administrar tu página web sin tocar código.

---

## 1. Acceso al Panel 🚶

1. Ve a **[dulcesmoment0s.netlify.app/admin](https://dulcesmoment0s.netlify.app/admin)**
2. Ingresa el **email y contraseña** que configuraste en Firebase (ver `TUTORIAL_SETUP.md` §3)
3. Si aún no tienes Firebase configurado, usa tu clave local
4. Accederás automáticamente al Dashboard

> 🔒 El sistema usa **Firebase Authentication** — tus credenciales son seguras y con sesión real con expiración.

## 2. Dashboard Pro — Tu Centro de Control 📊

El dashboard tiene un **sidebar collapsible** a la izquierda y **6 tabs** de gestión:

| Tab | Qué ves |
|-----|---------|
| 📊 **Resumen** | KPIs financieros (ventas, utilidad, IGV, proyección, ticket promedio), alertas de inventario |
| 🛒 **Productos** | Grid visual con edición inline de precio, toggles stock/destacado, búsqueda + filtro, botón "Agregar Producto" |
| 📦 **Pedidos** | **Pipeline visual** — columnas por estado (nuevo, confirmado, preparando, enviado, entregado). Cambia estado con un clic. Indicador 🔥 Firebase / 💾 Local |
| 🏷️ **Cupones** | Crear cupones con código/descuento/tipo, toggle activo/inactivo, eliminar |
| 🎨 **Tema** | Editor de colores (4 pickers), dark mode, galería de presets, **preview en vivo** del tema |
| 📈 **Analytics** | Comparación semanal (barras), hora pico, mejor día, Top 5 productos |

### Sidebar rápido
El sidebar tiene:
- 🔀 Accesos directos a cada tab (Resumen, Productos, Pedidos, Cupones, Tema, Analytics)
- 🚀 Navegación rápida: Inicio, Menú, Builder, Tracker
- 🚪 Cerrar Sesión
- Colapsa a íconos-only con un clic

### Chatbot Admin (God Mode v3.0) 🤖
Cuando estás en el Dashboard, el chatbot Pastelito cambia a **modo CEO**. Además, el modo admin **no se pierde** al navegar a `/menu` o `/builder`.

> 🧠 **IA Autónoma (v5.0):** Pastelito ahora entiende el **significado** de tus preguntas gracias a un modelo de IA que corre directamente en tu navegador. No usa APIs externas — todo es local y privado.

**Finanzas:**
- 💰 Calcular tus **ventas totales**
- 📉 Analizar tu **rentabilidad**
- 🇵🇪 Calcular **IGV (SUNAT)**
- 🔮 Darte **proyecciones de cierre**
- 📦 Revisar tu **inventario**

**Analytics v2.0:**
- 📈 Comparación semanal: *"¿Cómo van las ventas?"*
- ⏰ Hora pico: *"¿Cuál es mi hora pico?"*
- 📅 Mejor día: *"¿Qué día vendo más?"*
- 🎫 Ticket promedio

**CEO Inteligente v3.0 (🆕):**
- 📊 Reporte ejecutivo: *"Dame un reporte"* → informe completo con ventas, ranking, anomalías y sugerencias
- 🏆 Ranking de productos: *"¿Qué producto se vende más?"* → Top 10 por ventas
- ⚠️ Detección de anomalías: *"¿Hay alertas?"* → detecta caídas, cero pedidos, dominio de producto
- 💡 Insights accionables: *"¿Cómo puedo mejorar?"* → sugerencias basadas en datos
- 🔮 Predicción de demanda: *"¿Cuánto voy a vender mañana?"* → estimación por día
- 📥 Exportar datos: *"Exportar datos"* → descarga CSV con historial de pedidos

**Wizards (paso a paso):**
- 🧁 *"Crear producto nuevo"* → Nombre → Precio → Categoría → Descripción → ✅
- 🏷️ *"Crear cupón"* → Código → Descuento → Tipo → ✅
- 🛵 *"Agregar zona"* → Nombre → Precio → ✅
- 📢 *"Crear banner"* → Texto → Link → ✅

**Alertas Proactivas:**
Al abrir el chat, Pastelito te avisa automáticamente si hay:
- 🔴 Productos agotados
- 📉 Caída de ventas
- 📅 Fechas especiales cercanas (San Valentín, Día de la Madre, Navidad, etc.)

**Memoria Inteligente (v3.0):**
Pastelito ahora recuerda el último producto que mencionaste. Si dices:
- *"Cuánto cuesta la chocoteja"* y luego *"sube el precio a 20"* → aplica a la chocoteja.

**Smart Fallback (v3.0):**
Si Pastelito no entiende un comando, sugiere hasta 3 acciones similares:
```
🤔 No entendí bien, jefe. ¿Quisiste decir alguno de estos?
• 💰 Cambiar precio
• ⭐ Destacar producto
• 📦 Cambiar stock
```

### 🎙️ Comandos por Voz (Nuevo v4.0)
¡Ahora puedes hablarle a Pastelito!
1. Presiona el ícono **🎤** en el chat.
2. Di tu comando (ej: *"Cambia precio del pionono a 80"*).
3. Pastelito transcribirá tu voz y ejecutará la acción.
*Perfecto para cuando estás cocinando y tienes las manos ocupadas.* 👨‍🍳

---

## 3. Gestión de Productos 🎂

### Opción 1: Desde el chatbot (Recomendado) 🤖
Abre el chatbot en modo admin y di:
- *"Crear producto nuevo"* → te guía paso a paso
- *"Sube el Pionono a 80 soles"* → cambia precios
- *"Agota el Cheesecake"* → cambia stock
- *"Pon el Pionono en oferta"* → destaca producto

### Opción 2: Editando archivos (Avanzado)
Para cambiar productos directamente, edita:

**`src/data/products.ts`**

| Qué hacer | Cómo |
|-----------|------|
| Cambiar precio | Modifica el valor de `price` |
| Agotar producto | Cambia `stock` a `'soldout'` |
| Reponer producto | Cambia `stock` a `'available'` |
| Pocas unidades | Cambia `stock` a `'low'` |
| Destacar producto | Cambia `featured` a `true` |
| Agregar producto | Agrega un objeto nuevo al array |

> 📸 Las fotos van en `public/img/products/`

---

## 4. Cupones y Promociones 🏷️

### Opción 1: Desde el chatbot (Recomendado) 🤖
Di *"Crear cupón"* y Pastelito te guía: código → descuento → tipo → confirmar.

O directamente: *"Crea cupón VERANO20 del 20%"* → lo crea al instante.

### Opción 2: Editando archivos
Los cupones están en el contexto dinámico. Los cupones base se definen en `SiteConfigContext`.

| Cupón | Descuento |
|-------|-----------|
| `PRIMERA10` | 10% off |
| `DULCE5` | S/5 off |
| `CUMPLE20` | 20% off |

Para agregar uno nuevo, agrega un objeto al array:
```typescript
{ code: 'VERANO15', discount: 15, type: 'percent' }
```

---

## 5. Gestión de Pedidos (Tab Pedidos) 📦

Desde la **Fase 20**, los pedidos se almacenan en **Firebase/Firestore** (con fallback a localStorage).

### Pipeline de Estados
Cada pedido pasa por estos estados:

| Estado | Color | Descripción |
|--------|-------|-------------|
| 🟡 **Nuevo** | Amarillo | Acaba de llegar |
| 🔵 **Confirmado** | Azul | Pago verificado |
| 🟠 **Preparando** | Naranja | En cocina |
| 🟣 **Enviado** | Púrpura | En camino al cliente |
| 🟢 **Entregado** | Verde | Completado ✅ |
| 🔴 **Cancelado** | Rojo | Cancelado ❌ |

### Cómo gestionar pedidos
1. Ve al **Tab Pedidos** en el Dashboard
2. Verás las tarjetas de pedido organizadas por estado
3. Haz clic en el **botón de estado** para avanzar al siguiente
4. El cliente puede ver el estado en `/tracker`
5. El indicador 🔥/💾 muestra si está en Firebase o localStorage

---

## 6. Recepción de Pedidos 📱

Tu sistema de ventas ahora es **híbrido**:

1. El cliente arma su carrito y va a Checkout
2. Llena sus datos y elige método de pago
3. Al enviar, el pedido se guarda en **Firestore** (o localStorage si Firebase no está configurado)
4. El cliente es redirigido a `/checkout/confirm` con el pipeline visual
5. *(Opcional)* Se envía notificación por WhatsApp
6. **Tú gestionas desde el Tab Pedidos:**
   - Confirma el pago (cambia a "confirmado")
   - Marca como "preparando" cuando entres a cocina
   - Marca como "enviado" al despachar
   - Marca como "entregado" al completar
   - ¡El cliente ve todo en tiempo real!

---

## 6. Feedback de Clientes ⭐

Después de entregar un pedido, envía este mensaje al cliente:
```
¡Hola! Gracias por tu pedido 🎂
¿Nos ayudas con 30 segundos?
👉 dulcesmoment0s.netlify.app/feedback
```

Las opiniones aparecerán en tu Dashboard automáticamente.

---

## 7. Preguntas Frecuentes

**¿Mis cambios se ven al instante?**
Tardan aprox. 1-2 minutos. Netlify reconstruye la página automáticamente después del push.

**¿Puedo ver el panel desde el celular?**
Sí, `/admin` funciona en celulares, aunque es más cómodo en PC.

**¿Qué pasa si subo una foto muy pesada?**
Trata de usar fotos de menos de 1MB para que la página cargue rápido.

**¿Dónde cambio el número de WhatsApp?**
En `src/app/checkout/page.tsx`, busca `51965968723`.

**¿Cómo activo los pagos con tarjeta?**
Ve a `TUTORIAL_SETUP.md` §5 y sigue los pasos para configurar Culqi.
Una vez que tengas las API keys, el botón de tarjeta aparecerá automáticamente en el Checkout.

**¿Cómo bloquear una fecha de pedido?**
En el chatbot admin escribe: *"Bloquea el [fecha]"*.
Ejemplo: *"Bloquea el 25 de diciembre"*.
