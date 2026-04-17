# 🏭 MOTOR MAESTRO (FABRICAWEB)
**Guía de Inicialización para Desarrolladores e Inteligencias Artificiales**

Este directorio (`F:\FABRICAWEB`) es el Boilerplate (Motor de Fábrica) del ecosistema web de alto rendimiento. Fue clonado desde *Antojitos Express* y sometido a un lavado de identidad para servir como cimiento en el cual crear INFINITOS comercios, catálogos, restaurantes o clínicas de forma inmediata sin reconstruir la rueda.

---

## 🏗️ 1. Arquitectura Interna
El boilerplate viene pre-equipado de fábrica con:
1. **Inteligencia Artificial (NLP)** autónoma y sin dependencias.
2. **Base de Datos Descentralizada (Gun.js)** para almacenamiento P2P y carrito offline.
3. **Panel de Administración en la sombra (`/admin`)** para analítica, edición de menús in-app y Cupones.
4. **Pasarela de Recaudación (Culqi)** (Actualmente stub, lista para interceptar API localmente).

---

## 🛠️ 2. ¿Cómo instanciar un Nuevo Negocio? (Pasos a Seguir)

Si vas a usar esta carpeta para crear un nuevo negocio, sigue este manual de forma estricta:

### Paso A: Renombrar el Identificador Global
Ve al archivo `src/context/SiteConfigContext.tsx` y localiza:
```typescript
const STORAGE_KEY = '<BUSINESS_ID>_config_v1';
const P2P_DB_NODE = '<BUSINESS_ID>';
```
Reemplaza `<BUSINESS_ID>` por el acrónimo del nuevo negocio (Ej: `ferreteria_juan`, `clinica_salud_v1`). Esto creará una burbuja segura en la base de datos descentralizada.

Luego edita la constante `defaultContent` en ese mismo archivo:
```typescript
{
    businessName: 'Nombre Real del Negocio',
    heroTitle: 'Título de la Web', ...
}
```

### Paso B: Construcción del Inventario
Abre `src/data/products.ts`. Actualmente contiene un `producto-demo-1`.
Diseña y agrega la data respectiva del nuevo negocio. No importa si es "Servicio de Limpieza" o "Zapatos", mantén la estructura `id`, `title`, `price` e `image`. Coloca las imágenes en `public/img/products/`.

### Paso C: Lavado de Cerebro del Chatbot IA
Para que el asistente adopte su nueva cara y personalidad corporativa, debes ajustar 3 archivos:
1. `src/components/Chatbot.tsx`: Cambia el Emoji 🤖 y texto genérico `<BRAND_MASCOT>` por el nombre de tu nuevo asesor.
2. `src/data/chatbot-kb.ts`: Ajusta la *Knowledge Base* para que el NLP responda preguntas específicas de los zapatos/ferretería/restaurante.
3. `src/data/chatbot-responses.ts`: Reemplaza respuestas quemadas genéricas si existieran.

### Paso D: Cambio de Estética
Accede al administrador oculto `/admin` usando la contraseña por defecto generada (SHA-256 en la variable `adminPassword`). Alternativamente, edita `defaultTheme` en `SiteConfigContext.tsx` para configurar `primary`, `secondary` y el `darkMode`.

---

## 🚀 3. Despliegue en Producción
Una vez finalices el Paso A, B, C y D:
1. Ejecuta `npm install` (Solo la primera vez, el directorio base no tiene la carpeta pesada de node_modules).
2. Ejecuta `npm run dev` para ver el proyecto operando.
3. Al finalizar todo, ejecuta `npm run build`.

Al igual que en *Antojitos Express*, el renderizador masticará todo tu robusto ecosistema React de `src`, y defecará en la raíz una solitaria carpeta llamada **`out`**. 
Esa carpeta contiene tu oro. Es todo lo que necesitas arrastrar a Netlify o cualquier CDN estático. ¡Jamás subas esta carpeta raíz completa, solo el `out`!
