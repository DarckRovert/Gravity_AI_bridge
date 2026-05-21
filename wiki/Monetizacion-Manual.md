# 💰 Manual de Monetización — Gravity AI Bridge V15.0 PRO

> Guía de referencia técnica y operativa para desplegar, configurar y maximizar la Content Factory autónoma y la suite de ingresos pasivos de Gravity AI Bridge V15.0 PRO Omniscient-Tier.

---

## 📋 Índice General
1.  [Visión General de la Content Factory](#1-visión-general-de-la-content-factory)
2.  [Arquitectura de Ingresos y CPM Geográfico](#2-arquitectura-de-ingresos-y-cpm-geográfico)
3.  [Módulo 1 — YouTube Autoproducción y OAuth v3](#3-módulo-1--youtube-autoproducción-y-oauth-v3)
4.  [Módulo 2 — Content Scheduler (Gestión de Nichos)](#4-módulo-2--content-scheduler-gestión-de-nichos)
5.  [Módulo 3 — Language Cloner (Clonación por SAPI/TTS)](#5-módulo-3--language-cloner-clonación-por-sapitts)
6.  [Módulo 4 — Affiliate Manager (Inserción de Enlaces CPA)](#6-módulo-4--affiliate-manager-inserción-de-enlaces-cpa)
7.  [Módulo 5 — Social Distribution (TikTok & Instagram Graph)](#7-módulo-5--social-distribution-tiktok--instagram-graph)
8.  [Módulo 6 — Revenue Tracker (Análisis Predictivo)](#8-módulo-6--revenue-tracker-análisis-predictivo)
9.  [React SPA Dashboard — Monetization Hub](#9-react-spa-dashboard--monetization-hub)
10. [Proyecciones Financieras (ES vs. Global EN)](#10-proyecciones-financieras-es-vs-global-en)
11. [Resolución de Problemas y Diagnósticos](#11-resolución-de-problemas-y-diagnósticos)

---

## 1. Visión General de la Content Factory

La suite de monetización integrada en **Gravity AI Bridge V15.0 PRO** opera sobre una arquitectura de cola distribuida asíncrona que optimiza al máximo los recursos de procesamiento (CPU/GPU) y automatiza el ciclo de vida de producción de video multilingüe:

-   **Videos de Alta Retención (8+ Minutos)**: El generador de guiones planifica y compone videos largos para habilitar los anuncios de mitad de video (*mid-roll ads*) en YouTube, incrementando el RPM real hasta en un **400%**.
-   **Clonación Sin Costo de Render (Language Cloner)**: Reutiliza la secuencia de imágenes y las transiciones ya renderizadas en el video original en español. El motor traduce el guion de manera asíncrona, regenera el audio clonado con la voz del idioma destino e interpola las pistas de música de fondo, entregando videos listos para el mercado global (Inglés, Portugués, Francés) con **0% de costo de procesamiento de imágenes**.
-   **Inserción Dinámica de Afiliados CPA**: Inyecta automáticamente los enlaces de afiliación correspondientes al nicho del video con llamadas a la acción (CTA) personalizadas en la descripción, monetizando los canales desde el primer día incluso antes de calificar para el Programa de Socios de YouTube (YPP).

```
[Flujo de Procesamiento y Monetización en V15.0 PRO]

                      Render GPU Original
                               │
                       Video 8+ min (ES)
                               │
          ┌────────────────────┼────────────────────┐
          ▼                    ▼                    ▼
   YouTube ES (SEO)      Short (58s) ES      Language Cloner (EN/PT)
   (Anuncios + Links)          │             (0% GPU Render adicional)
                               ├──────────────┐     │
                               ▼              ▼     ▼
                        YouTube Shorts    TikTok  YouTube Global
```

---

## 2. Arquitectura de Ingresos y CPM Geográfico

El sistema prioriza la subida en regiones geográficas de alto rendimiento publicitario (Tier 1).

| Canal / Métrica | CPM Promedio (ES) | CPM Promedio (EN - Tier 1) | Requisito de Activación |
| :--- | :--- | :--- | :--- |
| **YouTube Mid-Roll** | \$1.50 – \$4.50 | \$8.00 – \$15.00 | 1,000 Suscriptores + 4,000 Horas |
| **YouTube Shorts** | \$0.03 – \$0.08 | \$0.05 – \$0.10 | 10M de visualizaciones en Shorts |
| **Afiliados CPA (Links)** | Variable (EPC: \$2.50) | Variable (EPC: \$10.00) | Registro en Affiliate Manager (Sin mínimos) |
| **TikTok Creator Fund** | \$0.02 – \$0.04 | \$0.03 – \$0.06 | 10,000 Seguidores + 100k Vistas |

---

## 3. Módulo 1 — YouTube Autoproducción y OAuth v3

Este módulo interactúa directamente con la **YouTube Data API v3** para subir videos, incrustar miniaturas y estructurar descripciones con SEO automatizado.

### Configuración del Proyecto en Google Cloud
1.  Ingresa a [console.cloud.google.com](https://console.cloud.google.com).
2.  Crea un nuevo proyecto y habilita la **YouTube Data API v3**.
3.  Configura la pantalla de consentimiento OAuth y agrega los alcances de subida de videos (`youtube.upload`).
4.  Crea credenciales de tipo **ID de cliente de OAuth 2.0 (Aplicación de Escritorio)**.
5.  Descarga el archivo de credenciales en formato JSON y guárdalo en la ruta `_integrations/youtube_oauth.json` del puente.

### Estructura de Credenciales (`_integrations/youtube_oauth.json`)
```json
{
  "client_id": "TU_CLIENT_ID.apps.googleusercontent.com",
  "client_secret": "TU_CLIENT_SECRET",
  "access_token": "",
  "refresh_token": ""
}
```

### Configuración en `config.yaml`
```yaml
youtube:
  enabled: true
  auto_upload: true
  default_category: "28"      # 28 corresponde a "Ciencia y Tecnología"
  default_privacy: "public"
  quota_daily_limit: 50       # Controla el consumo del límite de cuota diaria de Google API
  oauth_credentials_path: "_integrations/youtube_oauth.json"
```

### Flujo de Autorización Único de API
El puente expone endpoints para automatizar el intercambio de tokens de forma interactiva:

1.  **Obtener URL de Autorización**:
    -   `GET http://localhost:7860/v1/youtube/auth/url`
    -   *Retorna la URL oficial de Google para loguearte y dar permisos al canal.*
2.  **Intercambiar Código de Verificación**:
    -   `POST http://localhost:7860/v1/youtube/auth/exchange`
    -   **Cuerpo (Body JSON)**:
        ```json
        {
          "code": "4/0AdQt8qh..."
        }
        ```
    -   *El puente procesa el código, obtiene el `access_token` y `refresh_token` y los inyecta encriptados en disco con protección DPAPI.*

---

## 4. Módulo 2 — Content Scheduler (Gestión de Nichos)

El planificador de contenido automatiza la generación diaria basándose en el archivo de nichos configurado en `niches_file`.

```yaml
scheduler:
  enabled: true
  time_utc: "08:00"
  videos_per_day: 2
  niches_file: "inputs/niches.json"
```

### Configuración del Banco de Nichos (`inputs/niches.json`)
El archivo JSON organiza los nichos de mercado con sus temas pendientes y metadatos financieros de referencia:

```json
[
  {
    "id": "tecnologia_ia",
    "topics": [
      "El impacto de los procesadores cuánticos",
      "Modelos de IA locales vs la nube"
    ],
    "style": "cinematico",
    "lang": "es",
    "bgm_type": "electronica_futurista",
    "n_scenes": 64,
    "estimated_cpm_usd": 12.5,
    "times_used": 0
  }
]
```

### Endpoints de API de Control de Nichos y Trigger Manual

#### 1. Añadir Temas a un Nicho
*   **Ruta**: `POST http://localhost:7860/v1/scheduler/topic/add`
*   **Cuerpo (Body JSON)**:
    ```json
    {
      "niche_id": "tecnologia_ia",
      "topic": "Las redes neuronales autoreguladas en V15.0 PRO"
    }
    ```
*   **Respuesta**:
    ```json
    {
      "ok": true,
      "message": "Tema añadido con éxito al nicho tecnologia_ia."
    }
    ```

#### 2. Disparar Producción Manual Inmediata
*   **Ruta**: `POST http://localhost:7860/v1/scheduler/trigger`
*   **Cuerpo (Body JSON)** (dejar en blanco para elegir automáticamente por rotación, o forzar un tema específico):
    ```json
    {
      "niche_id": "tecnologia_ia",
      "topic": "El impacto de los procesadores cuánticos"
    }
    ```

---

## 5. Módulo 3 — Language Cloner (Clonación por SAPI/TTS)

Optimiza la reutilización de imágenes renderizadas para canales en múltiples idiomas mediante síntesis de voz clonada local.

### Configuración en `config.yaml`
```yaml
language_cloner:
  enabled: true
  original_lang: "es"
  languages:
    - "en"
    - "pt"
    - "fr"
```

### Clonar un Video Terminado (Fuerza Manual)
*   **Ruta**: `POST http://localhost:7860/v1/language/clone`
*   **Cuerpo (Body JSON)**:
    ```json
    {
      "job_id": 42,
      "languages": ["en", "pt"]
    }
    ```
*   **Descripción**: El motor traduce los textos del archivo `/_videos/job_42/script.json` a los idiomas objetivo. Utiliza las librerías SAPI/TTS locales de Windows para grabar los nuevos audios, sincronizar los tiempos de las escenas con precisión matemática y exportar los archivos `.mp4` finales sin volver a computar los frames visuales.

---

## 6. Módulo 4 — Affiliate Manager (Inserción de Enlaces CPA)

Inyecta de forma inteligente ofertas y enlaces de afiliados en la descripción del video en función de la temática y categoría de cada nicho.

```yaml
affiliates:
  enabled: true
  max_links_per_video: 3
  ids:
    NordVPN: "gravity_darck"
    Binance: "gravity_darck"
    Hostinger: "gravity_darck"
    ExpressVPN: "gravity_darck"
    _default: "gravity_darck"
```

### Registrar un Programa de Afiliados Personalizado
*   **Ruta**: `POST http://localhost:7860/v1/affiliates/program/add`
*   **Cuerpo (Body JSON)**:
    ```json
    {
      "niche_id": "tecnologia_ia",
      "program": {
        "name": "CloudHosting PRO",
        "url_template": "https://hostinger.com/gravity?ref={aff_id}",
        "cta": "🚀 Monta tu servidor VPS con descuento usando el código 'gravity'",
        "epc_usd": 15.5,
        "category": "hosting"
      }
    }
    ```

---

## 7. Módulo 5 — Social Distribution (TikTok & Instagram Graph)

Configura la distribución multicanal de tus Shorts de 58 segundos de forma automatizada sobre redes secundarias móviles.

### TikTok API Direct Upload (`_integrations/tiktok_creds.json`)
```json
{
  "access_token": "TU_TIKTOK_OAUTH_TOKEN",
  "client_key": "TU_CLIENT_KEY",
  "client_secret": "TU_CLIENT_SECRET"
}
```

### Instagram Reels Graph Upload (`_integrations/instagram_creds.json`)
Dado que Instagram requiere una dirección URL expuesta y con certificado SSL de descarga pública para procesar videos en su API Graph:
```json
{
  "access_token": "TU_FACEBOOK_GRAPH_TOKEN",
  "ig_user_id": "TU_INSTAGRAM_BUSINESS_ACCOUNT_ID",
  "cdn_base_url": "https://cdn.tuservidor.com/shorts/"
}
```

---

## 8. Módulo 6 — Revenue Tracker (Análisis Predictivo)

El estimador de ingresos en tiempo real registra las métricas proyectadas basadas en la visualización real del reproductor de video de la API de YouTube y los valores históricos de CPM de los nichos.

### Métodos de Consulta de la API

#### 1. Obtener Resumen General de Ingresos
*   **Ruta**: `GET http://localhost:7860/v1/revenue/summary?days=30`
*   **Respuesta**:
    ```json
    {
      "days_analyzed": 30,
      "total_views": 85420,
      "estimated_earnings_usd": 384.39,
      "top_performing_niche": "tecnologia_ia",
      "affiliate_clicks": 1420
    }
    ```

#### 2. Obtener Historial Diario (Línea de Tiempo)
*   **Ruta**: `GET http://localhost:7860/v1/revenue/timeline?days=14`
*   *Devuelve un array temporal estructurado ideal para alimentar gráficas dinámicas de barras y líneas.*

#### 3. Top Videos de Mayor Rentabilidad
*   **Ruta**: `GET http://localhost:7860/v1/revenue/top`
*   *Retorna los 10 videos con mayor volumen de ingresos generados.*

---

## 9. React SPA Dashboard — Monetization Hub

El panel interactivo en **💰 Monetización → Monetization Hub** dentro de los **26 paneles** del dashboard React expone un control total visualizado en alta fidelidad y responsive:

-   **KPI Financial Metrics Cards**: Visualización instantánea de ganancias estimadas de los últimos 30 días, proyecciones a final de mes y tasa de conversión de clics de enlaces de afiliados.
-   **Interactive Timeline Chart**: Gráfico dinámico interactivo con filtros integrados de tiempo que desglosa el rendimiento diario.
-   **YouTube Connection Wizard**: Indicadores de estado visuales del ciclo OAuth de Google y del límite de cuota diaria restante.
-   **Active Scheduler Controllers**: Permite encender o apagar el scheduler del Content Factory, ver la hora programada y disparar ejecuciones de emergencia o manuales.
-   **Niches Optimization Hub**: Mapeo visual de los nichos configurados, mostrando los CPMs estimados, la cantidad de temas disponibles y botones directos para inyectar nuevos tópicos.

---

## 10. Proyecciones Financieras (ES vs. Global EN)

### Plan de Producción de Alta Consistencia (2 videos al día de 8 minutos)

#### Escenario Local (Público de Habla Hispana - Promedio CPM \$2.80)
-   **Mes 1 (60 videos)**: ~4,000 visualizaciones combinadas. Ingresos AdSense: \$6.20 USD + afiliados CPA: \$15.00 USD.
-   **Mes 3 (180 videos)**: ~32,000 visualizaciones combinadas. Ingresos AdSense: \$49.00 USD + afiliados CPA: \$120.00 USD.
-   **Mes 6 (360 videos)**: ~140,000 visualizaciones combinadas. Ingresos AdSense: \$215.00 USD + afiliados CPA: \$520.00 USD.
-   **Ingresos Combinados Est. Mes 6**: **\$735.00 USD / mensual**.

#### Escenario Global (Público de Habla Inglesa Tier 1 - Promedio CPM \$11.50)
-   **Mes 1 (60 videos)**: ~4,000 visualizaciones combinadas. Ingresos AdSense: \$25.30 USD + afiliados CPA: \$60.00 USD.
-   **Mes 3 (180 videos)**: ~32,000 visualizaciones combinadas. Ingresos AdSense: \$202.00 USD + afiliados CPA: \$480.00 USD.
-   **Mes 6 (360 videos)**: ~140,000 visualizaciones combinadas. Ingresos AdSense: \$885.00 USD + afiliados CPA: \$2,100.00 USD.
-   **Ingresos Combinados Est. Mes 6**: **\$2,985.00 USD / mensual**.

---

## 11. FAQ y Resoluciones de Diagnóstico Técnico

#### 🛑 Error: Falla la subida automática a YouTube (HTTP 403 Forbidden / Quota Exceeded)
*   **Causa**: Has superado los límites de subida de videos diarios permitidos por la API de desarrollo gratuita de Google Cloud (10,000 unidades diarias, donde cada subida consume ~1,600 unidades).
*   **Solución**: Aumenta el intervalo de tiempo del scheduler, disminuye la cantidad de videos producidos al día en `quota_daily_limit`, o solicita una ampliación de cuota gratuita en tu consola de desarrollador de Google Cloud.

#### 🎙️ Error: El Language Cloner genera videos traduciendo los subtítulos pero el audio se escucha en Español
*   **Causa**: Tu sistema operativo Windows Server no posee los paquetes de voz SAPI/TTS correspondientes al idioma destino instalados localmente.
*   **Solución**: En el VPS, dirígete a *Configuración → Hora e idioma → Voz → Administrar voces* y haz clic en *Agregar voces* para descargar e instalar los paquetes de idiomas correspondientes a Inglés (EN), Portugués (PT) y Francés (FR).

#### 🔗 Error: Los enlaces de afiliación no se muestran en las descripciones de los videos subidos
*   **Causa**: La variable `affiliates.enabled` está establecida en `false` en tu archivo `config.yaml`, o no posees ningún ID de afiliado configurado dentro del bloque `affiliates.ids` que corresponda a las marcas recomendadas para el nicho.
*   **Solución**: Habilita la bandera booleana en el archivo de configuración global e introduce tu ID asignada en `ids` (o configura la clave `_default` para aplicar tu enlace a cualquier programa).

---
*Manual de Operaciones y Monetización Pasiva — Gravity AI Bridge V15.0 PRO.*
