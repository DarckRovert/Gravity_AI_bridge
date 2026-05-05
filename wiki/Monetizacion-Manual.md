# 💰 Manual de Monetización — Gravity AI Bridge V12.2

> Guía completa para activar y operar el sistema de ingresos autónomos.

---

## Índice

1. [Visión General](#1-visión-general)
2. [Arquitectura de Ingresos](#2-arquitectura-de-ingresos)
3. [Módulo 1 — YouTube Auto-Upload](#3-módulo-1--youtube-auto-upload)
4. [Módulo 2 — Content Scheduler](#4-módulo-2--content-scheduler)
5. [Módulo 3 — Language Cloner](#5-módulo-3--language-cloner)
6. [Módulo 4 — Affiliate Manager](#6-módulo-4--affiliate-manager)
7. [Módulo 5 — Social Distribution](#7-módulo-5--social-distribution)
8. [Módulo 6 — Revenue Tracker](#8-módulo-6--revenue-tracker)
9. [Dashboard — Monetization Hub](#9-dashboard--monetization-hub)
10. [Proyección de Ingresos](#10-proyección-de-ingresos)
11. [FAQ y Resolución de Problemas](#11-faq-y-resolución-de-problemas)

---

## 1. Visión General

Gravity AI Bridge V12.2 incluye una **Content Factory** autónoma que:

- Genera videos de **8+ minutos** (activa mid-roll ads en YouTube → 4x más RPM)
- Sube automáticamente a **YouTube** con thumbnails CTR, SEO y afiliados en descripción
- Genera un **Short de 58s** de cada video y lo distribuye a **TikTok** e **Instagram**
- **Clona** el video traducido a inglés/portugués/francés usando las imágenes ya renderizadas
- **Registra** ingresos estimados por canal y nicho en el dashboard

```
GPU Render (1 vez)
    ↓
Video 8+ min (ES)
    ├── YouTube ES → ads + afiliados
    ├── Short → YouTube Shorts + TikTok + Instagram
    └── Language Cloner
            ├── YouTube EN → CPM 5x mayor
            └── YouTube PT → audiencia Brasil
```

---

## 2. Arquitectura de Ingresos

| Fuente | CPM (ES) | CPM (EN) | Activación |
|--------|----------|----------|-----------|
| YouTube Mid-Roll | $1.50–4.50 | $8–15 | Videos >8 min |
| YouTube Shorts | $0.03–0.08 | $0.05–0.10 | Automático |
| Afiliados CPA | Variable | Variable | Link en descripción |
| TikTok Creator Fund | $0.02–0.04 | $0.03–0.06 | 1000+ seguidores |

---

## 3. Módulo 1 — YouTube Auto-Upload

### Prerequisitos

1. Ve a [console.cloud.google.com](https://console.cloud.google.com)
2. Crea un proyecto → Habilita **YouTube Data API v3**
3. Crea credenciales **OAuth 2.0 para aplicación de escritorio**
4. Descarga el JSON de credenciales

### Configuración

Edita `_integrations/youtube_oauth.json`:

```json
{
  "client_id": "TU_CLIENT_ID.apps.googleusercontent.com",
  "client_secret": "TU_CLIENT_SECRET",
  "access_token": "",
  "refresh_token": ""
}
```

### Flujo de Autorización (una sola vez)

```bash
# 1. Obtener la URL de autorización
GET http://localhost:7860/v1/youtube/auth/url

# 2. Visitar la URL en el navegador, aprobar, copiar el código

# 3. Intercambiar el código por refresh_token
POST http://localhost:7860/v1/youtube/auth/exchange
Body: {"code": "4/TU_CODIGO_AQUI"}
```

### Activar en config.yaml

```yaml
youtube:
  enabled: true           # ← Activar
  default_privacy: public
  quota_daily_limit: 5    # Máximo 5 uploads/día (YouTube da 10K unidades/día)
```

### Columnas nuevas en DB (`_video_queue.sqlite`)

| Columna | Descripción |
|---------|-------------|
| `youtube_video_id` | ID del video en YouTube |
| `youtube_url` | URL completa del video |
| `upload_status` | pending / uploaded / failed / quota_exceeded |
| `uploaded_at` | Timestamp UTC del upload |
| `shorts_path` | Ruta del clip Short generado |
| `shorts_video_id` | ID del Short en YouTube |
| `seo_description` | Descripción generada con SEO |

---

## 4. Módulo 2 — Content Scheduler

El scheduler produce videos de forma autónoma a una hora fija cada día.

### Activar

```yaml
scheduler:
  enabled: true
  time_utc: "08:00"      # Ejecutar a las 03:00 AM México (UTC-5)
  videos_per_day: 2
```

### Banco de Nichos (`inputs/niches.json`)

Se crea automáticamente al primer arranque. Estructura por niche:

```json
{
  "id": "finanzas_personales",
  "topics": ["Cómo invertir desde cero", "..."],
  "style": "publicitario",
  "lang": "es",
  "bgm_type": "corporativo",
  "n_scenes": 64,
  "estimated_cpm_usd": 12.0,
  "times_used": 0
}
```

### Agregar temas vía API

```bash
POST http://localhost:7860/v1/scheduler/topic/add
Body: {"niche_id": "finanzas_personales", "topic": "Los 7 errores de inversión más comunes"}
```

### Trigger manual

```bash
POST http://localhost:7860/v1/scheduler/trigger
Body: {}  # selección automática

# O forzar un nicho y tema específico:
Body: {"niche_id": "tecnologia_ia", "topic": "El chip cuántico de Google"}
```

---

## 5. Módulo 3 — Language Cloner

**Reutiliza las imágenes ya renderizadas** (no gasta GPU) y solo regenera el audio en el nuevo idioma.

### Activar

```yaml
language_cloner:
  enabled: true
  languages:
    - en    # Inglés — CPM 5x mayor que español
    - pt    # Portugués Brasil — 200M+ de audiencia
  original_lang: es
```

### Requisitos

- SAPI debe tener voz del idioma instalada (Panel de Control → Opciones de accesibilidad → Síntesis de voz)
- El pipeline guarda automáticamente `script.json` en cada `_videos/job_N/` al terminar

### Clonar manualmente un job existente

```bash
POST http://localhost:7860/v1/language/clone
Body: {"job_id": 42, "languages": ["en", "pt"]}
```

---

## 6. Módulo 4 — Affiliate Manager

### Activar

```yaml
affiliates:
  enabled: true
  max_links_per_video: 3
  ids:
    NordVPN: "TU_ID_NORDVPN"
    Binance: "TU_ID_BINANCE"
    Curiosity Stream: "TU_CODIGO_CS"
```

### Dónde obtener los IDs

| Programa | URL de registro |
|----------|----------------|
| NordVPN | [affiliates.nordvpn.com](https://affiliates.nordvpn.com) |
| Binance | [binance.com/en/activity/affiliate](https://www.binance.com/en/activity/affiliate) |
| eToro | [etoro.com/partners](https://www.etoro.com/partners/) |
| Hostinger | [hostinger.com/affiliates](https://www.hostinger.com/affiliates) |
| Curiosity Stream | [go.curiositystream.com/affiliate](https://go.curiositystream.com/affiliate) |

### Agregar programas personalizados

```bash
POST http://localhost:7860/v1/affiliates/program/add
Body: {
  "niche_id": "tecnologia_ia",
  "program": {
    "name": "Mi Programa",
    "url_template": "https://ejemplo.com?ref={aff_id}",
    "cta": "🔥 Prueba gratis por 30 días",
    "epc_usd": 10.0,
    "category": "software"
  }
}
```

---

## 7. Módulo 5 — Social Distribution

### TikTok

1. Ve a [developers.tiktok.com](https://developers.tiktok.com)
2. Crea una App → Solicita el permiso `video.publish`
3. Completa el OAuth → copia el `access_token`
4. Edita `_integrations/tiktok_creds.json`:

```json
{
  "access_token": "TU_ACCESS_TOKEN",
  "client_key": "TU_CLIENT_KEY",
  "client_secret": "TU_CLIENT_SECRET"
}
```

5. Activa en `config.yaml`:

```yaml
social:
  tiktok:
    enabled: true
    privacy_level: PUBLIC_TO_EVERYONE
```

### Instagram Reels

> ⚠️ Instagram Graph API NO permite uploads directos. Necesitas una URL pública (CDN).

1. Crea App en [developers.facebook.com](https://developers.facebook.com) tipo "Business"
2. Agrega el producto "Instagram Graph API"
3. Genera un Long-Lived User Access Token
4. Configura un CDN (Cloudflare R2, AWS S3, etc.) para hospedar los videos temporalmente
5. Edita `_integrations/instagram_creds.json`:

```json
{
  "access_token": "TU_TOKEN",
  "ig_user_id": "TU_USER_ID",
  "cdn_base_url": "https://cdn.tudominio.com/videos/"
}
```

---

## 8. Módulo 6 — Revenue Tracker

El tracker estima automáticamente los ingresos basándose en CPM histórico por nicho.

### CPM base configurado

| Niche | CPM estimado (ES) |
|-------|------------------|
| finanzas_personales | $4.50 |
| tecnologia_ia | $3.20 |
| motivacion_exito | $2.80 |
| ciencia_naturaleza | $2.10 |
| misterios_conspiraciones | $1.90 |
| historia_mundial | $1.80 |

> YouTube retiene el 45% → RPM real = CPM × 0.55

### API de consulta

```bash
# Resumen de los últimos 30 días
GET http://localhost:7860/v1/revenue/summary?days=30

# Timeline diario (para gráficos)
GET http://localhost:7860/v1/revenue/timeline?days=14

# Top videos por ingreso
GET http://localhost:7860/v1/revenue/top
```

---

## 9. Dashboard — Monetization Hub

Accede desde el sidebar: **💰 Monetización → Monetization Hub**

### Secciones del panel

| Sección | Descripción |
|---------|-------------|
| **KPIs** | Ingreso 30d, proyección mensual, vistas totales, afiliados |
| **Timeline** | Gráfico de barras de ingresos diarios (14 días) |
| **YouTube** | Estado OAuth, quota diaria, botón de autorización |
| **Content Scheduler** | Estado, próxima ejecución, botón de trigger manual |
| **Social** | Estado TikTok/Instagram, uploads del día |
| **Affiliates** | Nichos cubiertos, programas configurados |
| **Language Cloner** | Idiomas activos, potencial de ingreso EN |
| **Por Niche** | Barras de ingresos por categoría |

---

## 10. Proyección de Ingresos

### Escenario conservador (solo ES, sin afiliados)

| Métrica | Mes 1 | Mes 3 | Mes 6 |
|---------|-------|-------|-------|
| Videos subidos | 60 | 180 | 360 |
| Vistas estimadas | 3,000 | 15,000 | 45,000 |
| **Ingreso YouTube** | **~$4** | **~$22** | **~$67** |

### Escenario optimizado (ES + EN + afiliados)

| Métrica | Mes 1 | Mes 3 | Mes 6 |
|---------|-------|-------|-------|
| Videos subidos (todos idiomas) | 120 | 360 | 720 |
| Vistas estimadas | 8,000 | 50,000 | 180,000 |
| Ingreso YouTube | ~$20 | ~$125 | ~$450 |
| Afiliados (1 click/50 views × $10 EPC) | ~$16 | ~$100 | ~$360 |
| **Total estimado** | **~$36** | **~$225** | **~$810** |

> Los primeros 1000 suscriptores + 4000 horas de watch time desbloquean la monetización de AdSense. Con 2 videos/día de 8 min, se alcanzan las 4000 horas en ~60-90 días.

---

## 11. FAQ y Resolución de Problemas

**P: El upload falla con HTTP 403**  
R: El `access_token` expiró. El sistema lo refresca automáticamente con el `refresh_token`. Si persiste, repite el flujo OAuth desde `/v1/youtube/auth/url`.

**P: El Language Cloner produce audio en español en lugar del idioma objetivo**  
R: La voz del idioma no está instalada en Windows. Ve a: *Panel de Control → Reconocimiento de voz → Opciones de voz → Agregar idiomas*.

**P: TikTok devuelve error de autenticación**  
R: El `access_token` de TikTok expira cada 24h. TikTok Developer no provee refresh tokens en cuentas personales; necesitas una cuenta de Business o Desarrollador verificada.

**P: El scheduler no encola videos aunque `enabled: true`**  
R: El scheduler duerme hasta la hora `time_utc`. Usa `POST /v1/scheduler/trigger` para forzar ejecución inmediata.

**P: ¿Por qué los ingresos del Revenue Tracker no coinciden con AdSense?**  
R: Son estimaciones basadas en CPM histórico. AdSense paga entre el día 21-26 del mes siguiente. Los valores reales variarán ±40% dependiendo de la audiencia geográfica real.

**P: ¿Cómo cambio el watermark?**  
R: Edita `config.yaml → branding.watermark_text`. El cambio aplica en el próximo video renderizado (el cache de branding se invalida al reiniciar el servidor).
