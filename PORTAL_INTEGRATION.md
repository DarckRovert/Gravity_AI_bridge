# GRAVITY REPORTER — Manual de Integración con el Portal

## Arquitectura del Sistema

```
F:\Gravity_AI_bridge\          ← Backend Python (Bridge Server + Daemon)
F:\gravity-news-portal\        ← Frontend React SPA (Netlify)
```

El **Orquestador (`news_daemon.py`)** ejecuta 3 workflows en rotación:

| Workflow | Frecuencia | Destino JSON |
|---|---|---|
| `reporter.json` | Cada ciclo (0.5–1h) | `src/data/news.json` |
| `essayist.json` | Cada 2 ciclos | `src/data/essays.json` |
| `scientist.json` | Cada 3 ciclos | `src/data/science.json` |

Tras publicar en el JSON, cada workflow ejecuta `GitDeploy` → push a GitHub → Netlify auto-deploya.

---

## Schema de Artículos por Tipo

### `news.json` — Noticias (`reporter.json`)

El **`ContentNormalizerNode`** produce automáticamente los campos `[AUTO]`. El LLM solo genera los `[LLM]`:

```json
{
  "id": "slug-del-titulo-abc123",
  "title": "...",
  "excerpt": "...",
  "fullText": "...",
  "category": "...",
  "region": "...",
  "featured": true,
  "tldr": ["Punto 1", "Punto 2"],
  "author": "Nexo Agora — Redaccion Periodistica",
  "date": "2026-07-07T02:00:00.000Z",
  "image": "/images/slug-abc123.jpg",
  "readingTime": 5,
  "tags": [],
  "type": "news"
}
```

Categorias validas para noticias:
Control Biometrico, Resistencia Digital, Soberania Criptografica, Vigilancia del Leviatan,
Tecnologia Descentralizada, Geopolitica y Macro-Leviatan, Medicina y Bioetica,
Cultura y Psicometria, Cine e Ingenieria Social, Deporte y Control Biometrico,
Ciencia y Sustrato, Religion y Creencias Masivas, Crimen de Estado y Abuso Policial

### `essays.json` — Ensayos (`essayist.json`)

```json
{
  "id": "...",
  "title": "...",
  "subtitle": "...",
  "excerpt": "...",
  "fullText": "...",
  "category": "...",
  "readingTime": 10,
  "featured": true,
  "author": "Nexo Agora — Redaccion Filosofica",
  "date": "...",
  "image": "...",
  "type": "essay"
}
```

Categorias validas: Filosofia y Soberania, Epistemologia, Economia Politica,
Psicologia Social, Tecnologia y Poder

### `science.json` — Ciencia (`scientist.json`)

```json
{
  "id": "...",
  "title": "...",
  "subtitle": "...",
  "excerpt": "...",
  "fullText": "...",
  "category": "...",
  "readingTime": 8,
  "featured": true,
  "author": "Nexo Agora — Redaccion Cientifica",
  "date": "...",
  "image": "...",
  "type": "science"
}
```

Categorias validas: Fisica y Cosmologia, Neurociencia, Biologia y Genetica,
Computacion Cuantica, Inteligencia Artificial, Clima y Ecosistemas, Medicina y Bioetica

---

## Sistema de Compartir — URL por Articulo

El portal genera URLs de comparticion por articulo en formato:
- Noticias:  https://gravitynewsportal.vercel.app/?article={id}
- Ciencia:   https://gravitynewsportal.vercel.app/ciencia?article={id}
- Ensayos:   https://gravitynewsportal.vercel.app/ensayos?article={id}

El ID lo genera el normalizer: slug(title)[:50] + "-" + md5(date)[:6]
El portal detecta ?article= al cargar y abre el modal/reader del articulo correspondiente.
El ID debe ser unico y estable — el normalizer lo garantiza.

---

## Rutas de Archivos Absolutas

| Proposito | Ruta |
|---|---|
| Noticias JSON | F:/gravity-news-portal/src/data/news.json |
| Ensayos JSON | F:/gravity-news-portal/src/data/essays.json |
| Ciencia JSON | F:/gravity-news-portal/src/data/science.json |
| Imagenes publicas | F:/gravity-news-portal/public/images/ |
| Repositorio Git | F:/gravity-news-portal/ |
| Estado del daemon | %LOCALAPPDATA%/Gravity/Databases/_periodista_state.json |
| Log del daemon | %LOCALAPPDATA%/Gravity/Logs/gravity.log |

---

## Markdown Soportado por el Portal (TypewriterMarkdown)

| Sintaxis | Resultado |
|---|---|
| ## Titulo | h2 con estilo markdown-h2 |
| ### Subtitulo | h3 con borde izquierdo |
| > Cita | blockquote |
| - item o * item | Lista con bullet |
| **negrita** | strong |
| *cursiva* | em |
| Linea en blanco | Espaciador de 10px |
| Cualquier texto | parrafo normal |

NO soportado: tablas, links [texto](url), imagenes, codigo inline, # H1

---

## Paginas del Portal y sus Rutas

| URL | Pagina | Fuente de datos |
|---|---|---|
| / | Home — BentoGrid de noticias | news.json |
| /geopolitica | Radar Geopolitico — filtrado por region | news.json |
| /ciencia | Ciencia y Sustrato — reader propio | science.json |
| /ensayos | Ensayos filosoficos — reader propio | essays.json |
| /books | Biblioteca | books.json (estatico) |

---

## Endpoints REST del Bridge (Puerto 7860)

| Endpoint | Metodo | Descripcion |
|---|---|---|
| /v1/journalist/status | GET | Estado del daemon |
| /v1/journalist/log | GET | Ultimas 100 lineas de log |
| /v1/journalist/news | GET | JSON actual de noticias |
| /v1/journalist/start | POST | Inicia el daemon |
| /v1/journalist/stop | POST | Detiene el daemon |

---

## Flujo Completo de Publicacion (reporter.json)

1. Daemon despierta (0.5-1h de intervalo)
2. RSSFeed obtiene titular real (Google News, BBC Mundo, Al Jazeera, The Intercept)
3. WebSearch busca contexto de la noticia en la web
4. RAGQuery busca en base de conocimiento local
5. LLM detector_propaganda analiza sesgos mediaticos
6. LLM postura_oficial genera perspectiva del statu quo
7. LLM postura_subversiva genera perspectiva critica del poder
8. LLM redactar_noticia sintetiza en JSON con fullText Markdown + referencias [X]
9. LLM editor_jefe edita y perfecciona el JSON
10. ContentNormalizerNode agrega id, date, image, readingTime, author
11. JSONAppender inserta en news.json (max 30 items, LIFO)
12. GitDeploy: git add . + git commit + git push → Netlify auto-deploya

---

## Campo tldr (Opcional en Noticias)

Si el LLM genera un campo "tldr" como array de strings en el JSON crudo, el portal
lo muestra en una caja destacada verde en la parte superior del articulo:

"tldr": [
  "El Leviatán expande su red biometrica a 12 nuevas ciudades",
  "Los contratos biometricos forzados ahora incluyen datos psicograficos",
  "La resistencia del Nexo Agora reporta 3 nodos comprometidos"
]

Si el campo no existe, el portal lo omite sin errores.

---

## Campo region (Requerido en Noticias)

Geopolitics.jsx filtra las noticias por region. Valores recomendados:
- Latinoamerica
- Norteamerica  
- Eurasia
- Medio Oriente
- Africa
- Asia-Pacifico
- Global

---

## Diagnostico Rapido

Si el articulo no aparece en el portal tras el ciclo:

1. Verificar _periodista_state.json → campo last_error
2. Revisar gravity.log → ultimas 50 lineas
3. Verificar que news.json fue actualizado (timestamp del archivo)
4. git -C F:/gravity-news-portal log --oneline -1 (verificar ultimo commit)
5. Verificar Netlify deploy status en el dashboard

---

## Notas Post-Refactor 2026-07-07

1. Compartir ahora copia al portapapeles la URL especifica del articulo (?article=id)
   Los IDs del normalizer son estables. No hay nada que cambiar en el workflow.

2. Science.jsx y Essays.jsx usan TypewriterMarkdown con animated=false para los readers.
   El fullText en Markdown del LLM se renderiza correctamente. Respetar la tabla de sintaxis.

3. ArticleModal tiene barra de progreso de lectura por scroll y controles de font-size.
   Estas mejoras son UI-only y no afectan los datos del reporter.

4. Las imagenes se descargan de Pollinations.ai y se guardan en public/images/{id}.jpg
   La ruta en el JSON es /images/{id}.jpg (ruta relativa al public/)
   Netlify sirve la imagen desde esa ruta correctamente.

5. El campo subtitle es requerido por Science.jsx y Essays.jsx para mostrarse en el reader.
   El normalizer lo pasa si el LLM lo genera. Los prompts de scientist y essayist ya lo piden.
