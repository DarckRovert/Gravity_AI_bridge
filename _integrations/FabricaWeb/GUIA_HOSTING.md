# 🌐 Guía de Publicación y Hosting

Tu proyecto "Dulces Momentos" está listo para salir al mundo. Aquí tienes las opciones:

## 1. Publicar en Netlify (Recomendado) ☁️

Tu sitio ya está configurado para Netlify con el archivo `netlify.toml`.

### Opción A: Con GitHub (automático)
1. Sube tu proyecto a un repositorio en [GitHub](https://github.com)
2. Crea una cuenta en [Netlify.com](https://www.netlify.com)
3. En Netlify: **"Add new site"** → **"Import an existing project"** → Selecciona tu repo
4. Netlify detecta el `netlify.toml` y configura todo automáticamente:
   - Build command: `npm run build`
   - Publish directory: `.next`
   - Base directory: `pastelito-next` (Si usas el repo completo)
5. Cada vez que hagas `git push`, tu sitio se actualiza solo

### Opción B: Deploy manual (arrastrando)
1. En tu terminal, ejecuta:
   ```bash
   npm run build
   ```
2. Ve a [app.netlify.com](https://app.netlify.com)
3. Arrastra la carpeta `pastelito-next` al panel de Netlify
4. Espera a que se despliegue (~1-2 minutos)

**Ventajas de Netlify:**
- ✅ Gratis (plan starter)
- ✅ HTTPS (candado seguro) automático
- ✅ CDN global (carga rápida en todo el mundo)
- ✅ Deploy automático con cada push
- ✅ Headers de seguridad configurados en `netlify.toml`

### URL actual
Tu sitio está publicado en: **[dulcesmoment0s.netlify.app](https://dulcesmoment0s.netlify.app)**

---

## 2. Desarrollo Local 🏠

Para ver tu sitio en tu computadora mientras desarrollas:

```bash
npm install        # Solo la primera vez
npm run dev        # Servidor de desarrollo
```

Abre **http://localhost:3000** en tu navegador.

> 💡 Los cambios que hagas en el código se reflejan al instante (hot reload).

---

## 3. Configuración del Deploy

El archivo `netlify.toml` en la raíz del proyecto controla la configuración:

```toml
[build]
  base = "pastelito-next"      # (Si despliegas desde la raíz del repo)
  command = "npm run build"     # Comando de construcción
  publish = ".next"             # Carpeta de salida

[[plugins]]
  package = "@netlify/plugin-nextjs"   # Plugin oficial

[[headers]]
  for = "/*"
  [headers.values]
    X-Frame-Options = "DENY"
    X-XSS-Protection = "1; mode=block"
    X-Content-Type-Options = "nosniff"
```

---

## 💡 Recomendación
- Usa **Netlify + GitHub** para producción — es lo más profesional y estable
- Usa **`npm run dev`** para desarrollo local y pruebas

---

## 4. Variables de Entorno Requeridas en Netlify

Ve a **Site settings → Environment variables** en Netlify y agrega:

| Variable | Dónde obtenerla |
|----------|----------------|
| `NEXT_PUBLIC_FIREBASE_API_KEY` | Firebase Console → Project Settings |
| `NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN` | Firebase Console → Project Settings |
| `NEXT_PUBLIC_FIREBASE_PROJECT_ID` | Firebase Console → Project Settings |
| `NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET` | Firebase Console → Project Settings |
| `NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID` | Firebase Console → Project Settings |
| `NEXT_PUBLIC_FIREBASE_APP_ID` | Firebase Console → Project Settings |
| `NEXT_PUBLIC_FIREBASE_VAPID_KEY` | Firebase → Project Settings → Cloud Messaging |
| `NEXT_PUBLIC_CULQI_PUBLIC_KEY` | Dashboard Culqi → Desarrolladores → API Keys |
| `CULQI_SECRET_KEY` | Dashboard Culqi → Desarrolladores → API Keys |

> ⚠️ `CULQI_SECRET_KEY` nunca debe ser pública. Solo Netlify (server-side) debe tenerla.
> 
> Para instrucciones detalladas de cómo obtener cada valor, lee **[TUTORIAL_SETUP.md](./TUTORIAL_SETUP.md)**.
